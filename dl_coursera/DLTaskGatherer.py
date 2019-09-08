import os
import zipfile
import io
import re
import logging

from .lib.ExploringTree import ExploringTree

from .markup import render_supplement

from .resource import load_resource
from .define import URL_ROOT
from .markup import CML


def _shorten_slug(x):
    if len(x['slug']) > 40:
        x['slug'] = x['slug'][:40]


class DLTaskGatherer:
    def __init__(self, *, soc, outdir):  # "soc" means "sepc or course"
        assert soc['type'] in ['Spec', 'Course']

        self._soc = soc
        self._outdir = outdir

        self._et = ExploringTree()
        self._resource_node = self._et.see('%s/resource' % self._soc['slug'])

        self._dl_tasks = []
        self._file_tasks = []

    def gather(self):
        (self._gather_spec if self._soc['type'] == 'Spec' else self._gather_course) (self._soc)

        _dir = self._path(self._resource_node.abspath()[1:])
        if not os.path.exists(_dir):
            with zipfile.ZipFile(io.BytesIO(load_resource('bundle.zip'))) as zf:
                zf.extractall(_dir)
            logging.info('new directory tree: %s' % _dir)

        for _ in self._file_tasks:
            data = _['data']
            filename = _['filename']
            if not os.path.exists(filename):
                os.makedirs(os.path.dirname(filename), exist_ok=True)
                with open(filename, 'wb') as ofs:
                    ofs.write(data)
                logging.info('new file: %s' % filename)

        return self._dl_tasks

    def _resource_path(self):
        return self._et.relpathTo(self._resource_node)

    def _path(self, s):
        return os.path.abspath(os.path.join(self._outdir, s))

    def _add_dl_task(self, url, s):
        self._dl_tasks.append({'url': url, 'filename': self._path(s)})

    def _add_file_task(self, data, s):
        self._file_tasks.append({'data': data, 'filename': self._path(s)})

    def _down(self, s, i=None):
        if i is None:
            self._et.down(s)
        else:
            self._et.down('%02d@%s' % (i + 1, s))

    def _see(self, s):
        return self._et.see(s).abspath()[1:]

    def _gather_spec(self, spec):
        with self._et:
            self._down(spec['slug'])

            for _i, course in enumerate(spec['courses']):
                self._gather_course(course, _i)

    def _gather_course(self, course, i=None):
        with self._et:
            self._down(course['slug'], i)

            self._gather_course_references(course)

            for _i, module in enumerate(course['modules']):
                self._gather_module(module, _i)

    def _gather_course_references(self, course):
        with self._et:
            self._down('references')

            refid2node = {}
            for i, ref in enumerate(course['references']):
                item = ref['item']
                if item['type'] == 'CML':
                    refid2node[ref['id']] = self._et.see('%02d@%s.html' % (i + 1, ref['slug']))

            def fn_a(a):
                _refid = a.get('refid')
                if not _refid:
                    return

                _node = refid2node.get(_refid)
                if not _node:
                    logging.warning('[fn_a] unknown _refid=%s\n%s' %
                                    (_refid, {_1: _2.abspath() for _1, _2 in refid2node.items()}))
                else:
                    a['href'] = self._et.relpathTo(_node)

            self._fn_a = fn_a

            for i, ref in enumerate(course['references']):
                item = ref['item']
                if item['type'] == 'CML':
                    self._gather_cml(item, i, ref)

    def _gather_module(self, module, i):
        _shorten_slug(module)

        with self._et:
            self._down(module['slug'], i)

            for _i, lesson in enumerate(module['lessons']):
                self._gather_lesson(lesson, _i)

    def _gather_lesson(self, lesson, i):
        _shorten_slug(lesson)

        with self._et:
            self._down(lesson['slug'], i)

            for _i, item in enumerate(lesson['items']):
                if item['type'] == 'Lecture':
                    self._gather_lecture(item, _i)
                elif item['type'] == 'Supplement':
                    self._gather_supplement(item, _i)

    def _gather_lecture(self, lecture, i):
        _shorten_slug(lecture)

        with self._et:
            self._down(lecture['slug'], i)

            for _i, video in enumerate(lecture['videos']):
                self._gather_video(video, _i)

            for asset in lecture['assets']:
                self._gather_asset(asset)

    def _gather_video(self, video, i):
        self._add_dl_task(video['url_video'], self._see('%02d@.mp4' % (i + 1)))
        if video.get('url_subtitle') is not None:
            self._add_dl_task(video['url_subtitle'], self._see('%02d@.srt' % (i + 1)))

    def _gather_supplement(self, supplement, i):
        _shorten_slug(supplement)

        with self._et:
            self._down(supplement['slug'], i)

            for _i, item in enumerate(supplement['items']):
                if item['type'] == 'CML':
                    self._gather_cml(item, _i, supplement)

    def _gather_cml(self, cml, i, supplement):
        import bs4
        html = cml['html']
        html = bs4.BeautifulSoup(html, 'html.parser')
        for a in html.find_all('a'):
            self._fn_a(a)
        html = str(html)

        data = render_supplement(content=html,
                                 resource_path=self._resource_path(),
                                 title='%s' % supplement['name']).encode('UTF-8')
        self._add_file_task(data, self._see('%02d@%s.html' % (i + 1, supplement['slug'])))

        for asset in cml['assets']:
            self._gather_asset(asset)

    def _gather_asset(self, asset):
        self._add_dl_task(asset['url'], self._see(asset['name']))
