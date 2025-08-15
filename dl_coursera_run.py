import logging
import argparse
import os
import pickle
import json
import sys
import textwrap

import requests

from tqdm import tqdm

import dl_coursera

from dl_coursera.lib.misc import change_ext, get_latest_app_version
from dl_coursera.lib.TaskScheduler import TaskScheduler
from dl_coursera.Crawler import Crawler
from dl_coursera.DLTaskGatherer import DLTaskGatherer
from dl_coursera.Downloader import DownloaderBuiltin
from dl_coursera.define import *


def _dir_cache(outdir, slug):
    return os.path.join(outdir, slug, '.cache')


def _file_log(outdir, slug):
    return os.path.join(_dir_cache(outdir, slug), 'main.log')


def _file_pkl_crawl(outdir, slug):
    return os.path.join(_dir_cache(outdir, slug), 'crawl.pkl')


def _file_json_gather(outdir, slug):
    return os.path.join(_dir_cache(outdir, slug), 'gather.json')


def _file_json_download_dl_tasks_failed(outdir, slug):
    return os.path.join(_dir_cache(outdir, slug), 'download.dl_tasks_failed.json')


def crawl(cookies_file, slug, outdir):
    file_pkl = _file_pkl_crawl(outdir, slug)
    if os.path.exists(file_pkl):
        with open(file_pkl, 'rb') as ifs:
            return pickle.load(ifs)

    with requests.Session() as sess:
        Crawler._login(sess, cookies_file=cookies_file)

        # Check whether the specialization/course exists

        if 'elements' in sess.get(URL_SPEC(slug)).json():
            isSpec = True
        elif 'elements' in sess.get(URL_COURSE_1(slug)).json():
            isSpec = False
        else:
            raise NotFoundExcepton(slug)

        # Check whether the cookies_file expires

        course = Course(slug=COURSE_0)
        d = sess.get(URL_COURSE_1(course['slug'])).json()
        course['id'] = d['elements'][0]['id']

        d = sess.get(URL_COURSE_REFERENCES(course['id'])).json()
        if d.get('errorCode') == 'Not Authorized':
            raise CookiesExpiredException()
        assert 'errorCode' not in d

    with TaskScheduler() as ts, requests.Session() as sess:
        with tqdm(
            desc='Crawling...',
            bar_format='{bar:31} [{percentage:3.0f}%] {n_fmt}/{total_fmt} {desc}',
        ) as bar:
            total = 0
            done = 0

            def _hook_add():
                nonlocal total
                total += 1
                bar.reset(total)
                bar.update(done)
                bar.refresh()

            def _hook_done():
                nonlocal done
                done += 1
                bar.update()
                bar.refresh()

            def _hook_retry():
                bar.refresh()

            ts.start(
                n_worker=1,
                hook_add=_hook_add,
                hook_done=_hook_done,
                hook_retry=_hook_retry,
            )
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
        json.dump(dl_tasks, ofs, indent=4)

    return dl_tasks


def download(dl_tasks, slug, outdir):
    file_json = _file_json_download_dl_tasks_failed(outdir, slug)
    if os.path.exists(file_json):
        with open(file_json, encoding='UTF-8') as ifs:
            dl_tasks = json.load(ifs)

    if len(dl_tasks) == 0:
        return

    with TaskScheduler() as ts:
        with tqdm(
            desc='Downloading...',
            bar_format='{bar:31} [{percentage:3.0f}%] {n_fmt}/{total_fmt} {desc}',
            total=len(dl_tasks),
        ) as bar:

            def _hook_done():
                bar.update(1)
                bar.refresh()

            def _hook_retry():
                bar.refresh()

            ts.start(n_worker=1, hook_done=_hook_done, hook_retry=_hook_retry)
            _cls_downloader = DownloaderBuiltin
            dl_tasks_failed = _cls_downloader(dl_tasks=dl_tasks, ts=ts).download()

    with open(file_json, 'w', encoding='UTF-8') as ofs:
        json.dump(dl_tasks_failed, ofs, indent=4)


def config_logger(logfile: str):
    logger = logging.getLogger()
    for _ in list(logger.handlers):
        logger.removeHandler(_)
    logger.setLevel(logging.NOTSET)

    stderrHandler = logging.StreamHandler()
    fileHandler = logging.FileHandler(filename=logfile, encoding='UTF-8', mode='w')

    logger.addHandler(stderrHandler)
    logger.addHandler(fileHandler)

    formatter = logging.Formatter(
        fmt='%(asctime)s - %(levelname)s - %(message)s',
        style='%',
        datefmt='%Y-%m-%d %H:%M:%S',
    )

    def _config_handler(h: logging.Handler, name: str, level: int):
        h.set_name(name)
        h.setFormatter(formatter)
        h.setLevel(level)

    _config_handler(stderrHandler, 'stderr', logging.ERROR)
    _config_handler(fileHandler, 'file', logging.INFO)


def main():
    parser = argparse.ArgumentParser(
        allow_abbrev=False,
        add_help=True,
        description='A simple, fast, and reliable Coursera crawling & downloading tool',
        epilog=textwrap.dedent(
            """
            If the command succeeds, you shall see `Done :-)`.
            If errors occur, visit `https://github.com/FLZ101/dl_coursera`
            for the troubleshooting guide.
            """
        ),
    )
    parser.add_argument('--cookies', required=True, help='path of the cookies file')
    parser.add_argument(
        '--outdir', default='.', help="the output directory. Default: `.'"
    )
    parser.add_argument(
        '--version', action='version', version='%%(prog)s %s' % dl_coursera.app_version
    )
    parser.add_argument('slug', help='slug of the specialization/course')

    args = vars(parser.parse_args())

    latest_version = get_latest_app_version()
    if latest_version > dl_coursera.app_version:
        msg = textwrap.dedent(
            f"A newer version {latest_version} is available.",
            file=sys.stderr,
        )
        print(msg, file=sys.stderr, flush=True)

    outdir = args['outdir']
    slug = args['slug']
    os.makedirs(_dir_cache(outdir, slug), exist_ok=True)

    config_logger(_file_log(outdir, slug))

    soc = crawl(args['cookies'], slug, outdir)

    dl_tasks = gather_dl_tasks(outdir, soc)

    download(dl_tasks, slug, outdir)

    sys.stderr.flush()
    print('Done :-)')


if __name__ == '__main__':
    main()
