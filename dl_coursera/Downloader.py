import subprocess
import os
import sys
import logging
import shutil
import xmlrpc.client

import requests
import jinja2

from .resource import load_resource


def _esc(s):
    return s.replace('\\', '\\\\').replace('"', '\\"')


class DownloaderCanNotWork(Exception):
    pass


class Downloader:
    def __init__(self, *, dl_tasks):
        self._dl_tasks = dl_tasks

    def download(self):
        pass

    def check(self):
        pass


class DownloaderTS(Downloader):
    def __init__(self, *args, ts, **kwargs):
        super().__init__(*args, **kwargs)

        self._ts = ts
        self._dl = ts.register_task(self._dl, ttl=3, desc='download')

    def _dl(self, *, url, filename):
        pass

    def download(self):
        self.check()

        for _ in self._dl_tasks:
            self._dl(url=_['url'], filename=_['filename'])

        failures = self._ts.wait()
        return [_1.kwargs for _1, _2 in failures]


class DownloaderBuiltin(DownloaderTS):
    def _dl(self, *, url, filename):
        os.makedirs(os.path.dirname(filename), exist_ok=True)

        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            r.raw.decode_content = True
            with open(filename, 'wb') as ofs:
                shutil.copyfileobj(r.raw, ofs)


class CheckExeMixIn:
    def _exe(self):
        pass

    def check(self):
        exe = self._exe()
        try:
            subprocess.run([exe, '--version'], stdout=subprocess.DEVNULL,
                           stderr=subprocess.STDOUT, check=True)
        except OSError:
            raise DownloaderCanNotWork('The executable %s is not installed or not in PATH' % exe)


class DownloaderSubprocess(CheckExeMixIn, DownloaderTS):
    def _dl(self, *, url, filename):
        subprocess.run(self._cmdline(url, filename), stdout=subprocess.DEVNULL,
                       stderr=subprocess.STDOUT, check=True)

    def _cmdline(self, url, filename):
        pass


class DownloaderCurl(DownloaderSubprocess):
    def _cmdline(self, url, filename):
        return ['curl', '--create-dirs', '--globoff', '--url', url, '--output', filename]

    def _exe(self):
        return 'curl'


class DownloaderAria2(DownloaderSubprocess):
    def _cmdline(self, url, filename):
        return ['aria2c',
                '--allow-overwrite=true',
                '--always-resume=true',
                '--auto-file-renaming=false',
                '--continue=true',
                '-d', os.path.dirname(filename),
                '-o', os.path.basename(filename),
                url]

    def _exe(self):
        return 'aria2c'


class DownloaderInput_file(Downloader):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._env = jinja2.Environment()
        self._env.filters['_dirname'] = lambda _: os.path.dirname(_)
        self._env.filters['_basename'] = lambda _: os.path.basename(_)
        self._env.filters['_esc'] = _esc

    def download(self):
        template = self._env.from_string(load_resource(self._template_path).decode('UTF-8'))
        return template.render(dl_tasks=self._dl_tasks)

    @property
    def _template_path(self):
        pass


class DownloaderCurl_input_file(DownloaderInput_file):
    @property
    def _template_path(self):
        return 'template/curl_input_file'


class DownloaderAria2_input_file(DownloaderInput_file):
    @property
    def _template_path(self):
        return 'template/aria2_input_file'


class DownloaderUget(CheckExeMixIn, Downloader):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def download(self):
        self.check()

        for _ in self._dl_tasks:
            _url = _['url']
            _filename = _['filename']
            cmdline = [self._exe(), '--quiet',
                       '--folder=%s' % os.path.dirname(_filename),
                       '--filename=%s' % os.path.basename(_filename), _url]
            subprocess.run(cmdline, stdout=subprocess.DEVNULL,
                           stderr=subprocess.STDOUT, check=True)

            logging.info('add downloading task: url=%s, filename=%s' % (_url, _filename))

    def _exe(self):
        return 'uget' if sys.platform == 'win32' else 'uget-gtk'


class DownloaderAria2_rpc(Downloader):
    def __init__(self, *args, url=None, secret=None, **kwargs):
        super().__init__(*args, **kwargs)

        self._client = xmlrpc.client.ServerProxy(url)
        self._secret = secret

    def download(self):
        self.check()

        for _ in self._dl_tasks:
            _url = _['url']
            _filename = _['filename']
            _args = [[_url], {'dir': os.path.dirname(_filename),
                              'out': os.path.basename(_filename),
                              'allow-overwrite': 'true',
                              'always-resume': 'true',
                              'auto-file-renaming': 'false',
                              'continue': 'true'}]
            if self._secret is not None:
                _args.insert(0, 'token:%s' % self._secret)

            self._client.aria2.addUri(*_args)
            logging.info('add downloading task: url=%s, filename=%s' % (_url, _filename))

    def check(self):
        try:
            self._client.system.listMethods()
        except ConnectionError:
            raise DownloaderCanNotWork('fail to connnect to the XML-RPC server')
