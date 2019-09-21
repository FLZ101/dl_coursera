import logging
import argparse
import os
import pickle
import json
import sys
import textwrap

import requests

import dl_coursera

from dl_coursera.lib.misc import change_ext, get_latest_app_version
from dl_coursera.lib.TaskScheduler import TaskScheduler
from dl_coursera.Crawler import Crawler
from dl_coursera.DLTaskGatherer import DLTaskGatherer
from dl_coursera.Downloader import (DownloaderAria2, DownloaderAria2_input_file, DownloaderAria2_rpc,
                                    DownloaderBuiltin, DownloaderCurl, DownloaderCurl_input_file,
                                    DownloaderUget)
from dl_coursera.define import *


def _file_pkl_crawl(outdir, slug):
    return os.path.join(outdir, '%s.crawl.pkl' % slug)


def _file_json_gather(outdir, slug):
    return os.path.join(outdir, '%s.gather.json' % slug)


def _file_json_download_dl_tasks_failed(outdir, slug):
    return os.path.join(outdir, '%s.download.dl_tasks_failed.json' % slug)


def _file_txt_download_input_file(outdir, slug, how):
    return os.path.join(outdir, '%s.download.%s_input_file.txt' % (slug, how))


def crawl(cookies_file, slug, isSpec, outdir, n_worker):
    file_pkl = _file_pkl_crawl(outdir, slug)
    if os.path.exists(file_pkl):
        with open(file_pkl, 'rb') as ifs:
            return pickle.load(ifs)

    with requests.Session() as sess:
        Crawler._login(sess, cookies_file=cookies_file)

        # Check whether the specialization/course exists

        if isSpec:
            if 'elements' not in sess.get(URL_SPEC(slug)).json():
                raise SpecNotExistExcepton(slug)
        else:
            if 'elements' not in sess.get(URL_COURSE_1(slug)).json():
                raise CourseNotExistExcepton(slug)

        # Check whether the cookies_file expires

        course = Course(slug=COURSE_0)
        d = sess.get(URL_COURSE_1(course['slug'])).json()
        course['id'] = d['elements'][0]['id']

        d = sess.get(URL_COURSE_REFERENCES(course['id'])).json()
        if d.get('errorCode') == 'Not Authorized':
            raise CookiesExpiredException()
        assert 'errorCode' not in d

    with TaskScheduler() as ts, requests.Session() as sess:
        ts.start(n_worker=n_worker)
        crawler = Crawler(ts=ts, sess=sess, cookies_file=cookies_file)
        soc = crawler.crawl(slug=slug, isSpec=isSpec)

    with open(file_pkl, 'wb') as ofs:
        pickle.dump(soc, ofs)

    file_json = change_ext(file_pkl, 'json')
    with open(file_json, 'w', encoding='UTF-8') as ofs:
        ofs.write(soc.to_json())

    return soc


def gather_dl_tasks(outdir, soc):
    file_json = _file_json_gather(outdir, soc['slug'])
    if os.path.exists(file_json):
        with open(file_json, encoding='UTF-8') as ifs:
            return json.load(ifs)

    dl_tasks = DLTaskGatherer(soc=soc, outdir=outdir).gather()
    with open(file_json, 'w', encoding='UTF-8') as ofs:
        json.dump(dl_tasks, ofs)

    return dl_tasks


def download_ts(dl_tasks, slug, outdir, how):
    file_json = _file_json_download_dl_tasks_failed(outdir, slug)
    if os.path.exists(file_json):
        with open(file_json, encoding='UTF-8') as ifs:
            dl_tasks = json.load(ifs)

    if len(dl_tasks) == 0:
        return

    with TaskScheduler() as ts:
        ts.start(n_worker=4)

        _cls_downloader = {'builtin': DownloaderBuiltin,
                           'curl': DownloaderCurl,
                           'aria2': DownloaderAria2}[how]
        dl_tasks_failed = _cls_downloader(dl_tasks=dl_tasks, ts=ts).download()

    with open(file_json, 'w', encoding='UTF-8') as ofs:
        json.dump(dl_tasks_failed, ofs)


def download_input_file(dl_tasks, slug, outdir, how):
    _cls_downloader = {'curl': DownloaderCurl_input_file,
                       'aria2': DownloaderAria2_input_file}[how]
    s = _cls_downloader(dl_tasks=dl_tasks).download()

    file_txt = _file_txt_download_input_file(outdir, slug, how)
    with open(file_txt, 'w', encoding='UTF-8') as ofs:
        ofs.write(s)
    logging.info('new file: %s' % file_txt)


def main():
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(threadName)s - %(message)s')

    parser = argparse.ArgumentParser(allow_abbrev=False, add_help=True,
        description="A simple, fast, and reliable Coursera crawling & downloading tool",
        epilog=textwrap.dedent('''
            If the command succeeds, you shall see `Done :-)`.
            If some UNEXPECTED errors occur, try decreasing the value of @--n-worker
            and/or removing the directory @--outdir.
            For more information, visit `https://github.com/feng-lei/dl_coursera`.
        ''')
    )
    parser.add_argument('--version', action='version', version='%%(prog)s %s' % dl_coursera.app_version)
    parser.add_argument('--cookies', help='path of the `cookies.txt`')
    parser.add_argument('--slug', required=True,
        help='slug of a course or a specializtion (with @--isSpec)')
    parser.add_argument('--isSpec', action='store_true',
        help='indicate that @--slug is slug of a specialization')
    parser.add_argument('--n-worker', type=int, default=3, choices=range(1, 6),
        help='the number of threads used to crawl webpages. Default: 3')

    parser.add_argument('--outdir', default='.',
        help='the directory to save files to. Default: `.\'')
    parser.add_argument('--how', required=True,
        choices=['builtin', 'curl', 'aria2', 'aria2-rpc', 'uget', 'dummy'],
        help='''how to download files.
                builtin (NOT recommonded): use the builtin downloader.
                curl: invoke `curl` or generate an "input file" for it (with @--generate-input-file).
                aria2: invoke `aria2c` or generate an "input file" for it (with @--generate-input-file).
                aria2-rpc (HIGHLY recommonded): add downloading tasks to aria2 through its XML-RPC interface.
                uget (recommonded): add downloading tasks to the uGet Download Manager'''
    )
    parser.add_argument('--generate-input-file', action='store_true',
        help='''when @--how is curl/aria2, indicate that to generate an "input file"
                for that tool, rather than to invoke it''')
    parser.add_argument('--aria2-rpc-url', default='http://localhost:6800/rpc',
        help="url of the aria2 XML-RPC interface. Default: `http://localhost:6800/rpc'")
    parser.add_argument('--aria2-rpc-secret', help='authorization token of the aria2 XML-RPC interface')

    args = vars(parser.parse_args())

    latest_version = get_latest_app_version()
    if latest_version > dl_coursera.app_version:
        print('dl_coursera version %s is obsolete. ' % dl_coursera.app_version +
              'You can upgrade it to version %s via `pip install -U dl_coursera`.' % latest_version)
        return

    os.makedirs(args['outdir'], exist_ok=True)

    soc = crawl(args['cookies'], args['slug'], args['isSpec'], args['outdir'], args['n_worker'])

    dl_tasks = gather_dl_tasks(args['outdir'], soc)

    if args['how'] == 'builtin':
        download_ts(dl_tasks, args['slug'], args['outdir'], args['how'])

    elif args['how'] in ['curl', 'aria2']:
        if args['generate_input_file']:
            download_input_file(dl_tasks, args['slug'], args['outdir'], args['how'])
        else:
            download_ts(dl_tasks, args['slug'], args['outdir'], args['how'])

    elif args['how'] == 'aria2-rpc':
        DownloaderAria2_rpc(dl_tasks=dl_tasks,
                            url=args['aria2_rpc_url'],
                            secret=args['aria2_rpc_secret']).download()

    elif args['how'] == 'uget':
        DownloaderUget(dl_tasks=dl_tasks).download()

    print('', flush=True, end='')
    print('\nDone :-)')


if __name__ == '__main__':
    main()
