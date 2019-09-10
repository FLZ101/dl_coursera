import os
import argparse
import json
import logging

from dl_coursera.lib.TaskScheduler import TaskScheduler
from dl_coursera.Downloader import (DownloaderAria2, DownloaderAria2_input_file, DownloaderAria2_rpc,
                                    DownloaderBuiltin, DownloaderCurl, DownloaderCurl_input_file,
                                    DownloaderUget)


_urls = ['https://www.jpl.nasa.gov/spaceimages/images/largesize/PIA22569_hires.jpg',
         'https://www.jpl.nasa.gov/spaceimages/images/largesize/PIA22359_hires.jpg',
         'https://www.jpl.nasa.gov/spaceimages/images/largesize/PIA22358_hires.jpg',
         'https://www.jpl.nasa.gov/spaceimages/images/largesize/PIA22567_hires.jpg',
         'https://www.jpl.nasa.gov/spaceimages/images/largesize/PIA22568_hires.jpg',
         'https://www.jpl.nasa.gov/spaceimages/images/largesize/PIA22356_hires.jpg',
         'https://www.jpl.nasa.gov/spaceimages/images/largesize/PIA22355_hires.jpg',
         'https://www.jpl.nasa.gov/spaceimages/images/largesize/PIA22353_hires.jpg',
         'https://www.jpl.nasa.gov/spaceimages/images/largesize/PIA22352_hires.jpg',
         'https://www.jpl.nasa.gov/spaceimages/images/largesize/PIA21423_hires.jpg']

_outdir = '__data/example/downloader'


def _file_json_dl_tasks_failed(how):
    return os.path.join(_outdir, how, 'dl_tasks_failed.json')


def _file_txt_input_file(how):
    return os.path.join(_outdir, how, 'input_file.txt')


def get_dl_tasks(how):
    return [{'url': url, 'filename': os.path.abspath(os.path.join(_outdir, how, 'dum', 'my', '%02d.jpg' % i))} for i, url in enumerate(_urls)]


def download_ts(dl_tasks, how):
    file_json = _file_json_dl_tasks_failed(how)

    with TaskScheduler() as ts:
        ts.start(n_worker=4)

        _cls_downloader = {'builtin': DownloaderBuiltin,
                           'curl': DownloaderCurl,
                           'aria2': DownloaderAria2}[how]
        dl_tasks_failed = _cls_downloader(dl_tasks=dl_tasks, ts=ts).download()

    with open(file_json, 'w', encoding='UTF-8') as ofs:
        json.dump(dl_tasks_failed, ofs)


def download_input_file(dl_tasks, how):
    _cls_downloader = {'curl': DownloaderCurl_input_file,
                       'aria2': DownloaderAria2_input_file}[how]
    s = _cls_downloader(dl_tasks=dl_tasks).download()

    file_txt = _file_txt_input_file(how)
    with open(file_txt, 'w', encoding='UTF-8') as ofs:
        ofs.write(s)
    logging.info('new file: %s' % file_txt)


def main():
    parser = argparse.ArgumentParser(allow_abbrev=False, add_help=True)
    parser.add_argument('--how', required=True,
        choices=['builtin', 'curl', 'aria2', 'aria2-rpc', 'uget'],
        help='''how to download files.
                builtin (NOT recommonded): use the builtin downloader.
                curl: invoke the `curl' tool or generate an "input file" for that
                      tool (with @--generate-input-file).
                aria2: invoke the `aria2c' tool or generate an "input file" for that
                      tool (with @--generate-input-file).
                aria2-rpc (HIGHLY recommonded): add downloading tasks to aria2
                      through its XML-RPC interface.
                uget (recommonded): add downloading tasks to the uGet Download Manager'''
    )
    parser.add_argument('--generate-input-file', action='store_true',
        help='''when @--how is curl/aria2, indicate that to generate an "input file"
                for that tool, rather than to invoke it''')
    parser.add_argument('--aria2-rpc-url', default='http://localhost:6800/rpc',
        help="url of the aria2 XML-RPC interface. Default: `http://localhost:6800/rpc'")
    parser.add_argument('--aria2-rpc-secret', help='authorization token of the aria2 XML-RPC interface')

    args = vars(parser.parse_args())

    os.makedirs(os.path.join(_outdir, args['how']), exist_ok=True)

    dl_tasks = get_dl_tasks(args['how'])

    if args['how'] == 'builtin':
        download_ts(dl_tasks, args['how'])

    elif args['how'] in ['curl', 'aria2']:
        if args['generate_input_file']:
            download_input_file(dl_tasks, args['how'])
        else:
            download_ts(dl_tasks, args['how'])

    elif args['how'] == 'aria2-rpc':
        DownloaderAria2_rpc(dl_tasks=dl_tasks,
                            url=args['aria2_rpc_url'],
                            secret=args['aria2_rpc_secret']).download()

    elif args['how'] == 'uget':
        DownloaderUget(dl_tasks=dl_tasks).download()

    print('\nDone :-)')


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO,
                        format='%(levelname)s - %(asctime)s - %(threadName)s - %(message)s')
    main()
