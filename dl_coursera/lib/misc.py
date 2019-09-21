import os
import tempfile

def format_dict(d):
    return ', '.join(['%s=%s' % (k, v) for k, v in d.items()])


def change_ext(filename, ext):
    return os.path.splitext(filename)[0] + ('' if ext == '' else '.' + ext)


def url_basename(url, *, _d={}):
    import re
    from urllib.parse import urlparse

    if _d.get('pat') is None:
        _d['pat'] = re.compile(r'([^/]*)$')

    match = _d['pat'].search(urlparse(url).path)
    return match.group(1)


class TmpFile:
    def __init__(self, suffix=None, prefix=None, dir=None):
        self._suffix = suffix
        self._prefix = prefix
        self._dir = dir

    def __enter__(self):
        fd, filename = tempfile.mkstemp(self._suffix, self._prefix, self._dir)
        os.close(fd)

        self._filename = filename
        return filename

    def __exit__(self, exc_type, exc_value, traceback):
        # os.remove(self._filename)
        pass


def get_latest_app_version():
    import requests
    resp = requests.get('https://pypi.org/pypi/dl-coursera/json')
    d = resp.json()

    return sorted(d['releases'].keys())[-1]
