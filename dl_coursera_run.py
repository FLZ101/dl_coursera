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

from dl_coursera.lib.misc import (
    change_ext,
    get_latest_app_version,
    get_current_app_version,
)
from dl_coursera.lib.TaskScheduler import TaskScheduler
from dl_coursera.Crawler import Crawler, login
from dl_coursera.DLTaskGatherer import DLTaskGatherer
from dl_coursera.Downloader import DownloaderBuiltin
from dl_coursera.define import *


def _dir_cache(outdir, slug):
    return os.path.join(outdir, slug, '.cache')


def _file_log(outdir, slug):
    return os.path.join(_dir_cache(outdir, slug), 'main.log')


def _file_pkl_crawl(outdir, slug):
    return os.path.join(_dir_cache(outdir, slug), 'crawl.pkl')


def _file_json_options(outdir, slug):
    return os.path.join(_dir_cache(outdir, slug), 'options.json')


def _options_for_cache(args):
    return {'quiz': args['quiz']}


def _parse_subtitles(value):
    if not value:
        return None
    langs = value.split(',')
    if any(not lang or lang != lang.strip() for lang in langs):
        raise argparse.ArgumentTypeError(
            '--subtitles must be comma-separated language codes without spaces'
        )
    return langs


def _refresh_cache(outdir, slug, args):
    """Invalidate the crawl cache when crawl-affecting options change."""

    options = _options_for_cache(args)
    options_file = _file_json_options(outdir, slug)

    old_options = None
    if os.path.exists(options_file):
        try:
            with open(options_file, encoding='UTF-8') as ifs:
                old_options = json.load(ifs)
        except (OSError, ValueError):
            pass

    if old_options == options:
        return

    file_pkl = _file_pkl_crawl(outdir, slug)
    cache_files = {file_pkl, change_ext(file_pkl, 'json')}

    if old_options is not None and old_options.get('quiz') == options.get('quiz'):
        cache_files = set()

    for filename in cache_files:
        try:
            os.remove(filename)
        except FileNotFoundError:
            pass

    with open(options_file, 'w', encoding='UTF-8') as ofs:
        json.dump(options, ofs, indent=4)


def crawl(cookies_file, slug, outdir, is_spec, include_quiz=False):
    file_pkl = _file_pkl_crawl(outdir, slug)
    if os.path.exists(file_pkl):
        with open(file_pkl, 'rb') as ifs:
            return pickle.load(ifs)

    with requests.Session() as sess:
        login(sess, cookies_file=cookies_file)

        # Check whether the specialization/course exists

        if is_spec:
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
            crawler = Crawler(
                ts=ts,
                sess=sess,
                cookies_file=cookies_file,
                include_quiz=include_quiz,
            )
            soc = crawler.crawl(slug=slug, is_spec=is_spec)

    with open(file_pkl, 'wb') as ofs:
        pickle.dump(soc, ofs)

    file_json = change_ext(file_pkl, 'json')
    with open(file_json, 'w', encoding='UTF-8') as ofs:
        ofs.write(soc.to_json())

    return soc


def gather_dl_tasks(outdir, soc, subtitle_langs=None):
    return DLTaskGatherer(
        soc=soc, outdir=outdir, subtitle_langs=subtitle_langs
    ).gather()


def download(dl_tasks):
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
            _cls_downloader(dl_tasks=dl_tasks, ts=ts).download()


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
        epilog=textwrap.dedent("""
            If the command succeeds, you shall see `Done :-)`.
            If errors occur, visit `https://github.com/FLZ101/dl_coursera`
            for the troubleshooting guide.
            """),
    )
    parser.add_argument(
        '--cookies',
        required=True,
        metavar='COOKIES_FILE',
        help='path of the cookies file',
    )
    parser.add_argument(
        '--outdir', default='.', help="the output directory. Default: `.'"
    )
    parser.add_argument(
        '--spec', action='store_true', help='indicate that @slug is of a specialization'
    )
    parser.add_argument(
        '--quiz',
        action='store_true',
        help='include quizzes',
    )
    parser.add_argument(
        '--subtitles',
        metavar='LANGUAGES',
        default=None,
        type=_parse_subtitles,
        help=(
            'comma-separated subtitle language codes without spaces, e.g. `en,zh-CN\'. '
            'Typical codes: en, zh-CN, es, fr, de, pt-BR, ja, ko, ru, it, ar, hi. '
            'Default: download the only available language; otherwise English if available.'
        ),
    )
    parser.add_argument(
        '--version', action='version', version='%%(prog)s %s' % dl_coursera.app_version
    )
    parser.add_argument('slug', help='slug of the specialization/course')

    args = vars(parser.parse_args())

    latest_version = get_latest_app_version()
    current_version = get_current_app_version()
    if latest_version > current_version:
        msg = textwrap.dedent(
            f"A newer version {latest_version} is available.",
        )
        print(msg, file=sys.stderr, flush=True)

    outdir = args['outdir']
    slug = args['slug']
    os.makedirs(_dir_cache(outdir, slug), exist_ok=True)

    config_logger(_file_log(outdir, slug))
    _refresh_cache(outdir, slug, args)

    soc = crawl(args['cookies'], slug, outdir, args['spec'], args['quiz'])

    dl_tasks = gather_dl_tasks(outdir, soc, args['subtitles'])

    download(dl_tasks)

    sys.stderr.flush()
    print('Done :-)')


if __name__ == '__main__':
    main()
