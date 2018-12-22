import pickle
import os
import logging

from .define import *

from .lib.misc import format_dict
from .markup import CML

PRIO_SPEC = 'A'
PRIO_COURSE = 'B'
PRIO_COURSE_MATERIAL = 'C'


class Crawler:
    def __init__(self, *, ts, sess, email, password):
        self._ts = ts

        def attach(func):
            setattr(self, func.__name__, func)
            return func

        @attach
        def login():
            resp = sess.get(URL_ROOT)
            resp = sess.post(URL_LOGIN(resp.cookies['CSRF3-Token']),
                             data={'email': email, 'password': password})

            assert resp.status_code == 200

        @attach
        @ts.register_task(
            priority=PRIO_SPEC, ttl=3,
            format_kwargs=lambda _: format_dict({'spec': _['spec']['slug']})
        )
        def crawl_spec(*, spec):
            resp = sess.get(URL_SPEC(spec['slug']))
            d = resp.json()

            _ = d['elements'][0]
            spec['id'] = _['id']
            spec['name'] = _['name']

            assert spec['slug'] == _['slug']

            for id_ in _['courseIds']:
                spec['courses'].append(Course(id_=id_))

            id2slug = {}
            for _ in d['linked']['courses.v1']:
                id2slug[_['id']] = _['slug']

            for _ in spec['courses']:
                _['slug'] = id2slug[_['id']]

            logging.info('Courses of specialization %s: %s' % (
                spec['slug'],
                ', '.join([_['slug'] for _ in spec['courses']])
            ))

            for _ in spec['courses']:
                crawl_course(course=_)

        @attach
        @ts.register_task(
            priority=PRIO_COURSE, ttl=3,
            format_kwargs=lambda _: format_dict({'source': _['course']['slug']})
        )
        def crawl_course(*, course):
            resp = sess.get(URL_COURSE_1(course['slug']))
            d = resp.json()

            _ = d['elements'][0]
            course['name'] = _['name']
            course['id'] = _['id']

            assert course['slug'] == _['slug']

            resp = sess.get(URL_COURSE_2(course['slug']))
            d = resp.json()['linked']

            id2item = {}
            for _ in d['onDemandCourseMaterialItems.v2']:
                typeName = _['contentSummary']['typeName']
                if typeName == 'lecture':
                    id2item[_['id']] = CourseMaterialLecture(id_=_['id'], name=_['name'], slug=_['slug'])
                elif typeName == 'notebook':
                    id2item[_['id']] = CourseMaterialNotebook(id_=_['id'], name=_['name'], slug=_['slug'])
                elif typeName == 'supplement':
                    id2item[_['id']] = CourseMaterialSupplement(id_=_['id'], name=_['name'], slug=_['slug'])

            id2lesson = {}
            for _ in d['onDemandCourseMaterialLessons.v1']:
                lesson = CourseMaterialLesson(id_=_['id'], name=_['name'], slug=_['slug'])
                for id_item in _['itemIds']:
                    item = id2item.get(id_item)
                    if item is not None:
                        lesson['items'].append(item)

                if len(lesson['items']) > 0:
                    id2lesson[lesson['id']] = lesson

            for _ in d['onDemandCourseMaterialModules.v1']:
                module = CourseMaterialModule(id_=_['id'], name=_['name'], slug=_['slug'])

                for id_ in _['lessonIds']:
                    lesson = id2lesson.get(id_)
                    if lesson is not None:
                        module['lessons'].append(lesson)

                if len(module['lessons']) > 0:
                    course['modules'].append(module)

            for module in course['modules']:
                for lesson in module['lessons']:
                    for item in lesson['items']:
                        if item['type'] == 'Lecture':
                            crawl_lecture(course=course, lecture=item)
                        elif item['type'] == 'Supplement':
                            crawl_supplement(course=course, supplement=item)

        @ts.register_task(
            priority=PRIO_COURSE_MATERIAL, ttl=3,
            format_kwargs=lambda _: format_dict({'course': _['course']['slug'],
                                                 'lecture': _['lecture']['slug']})
        )
        def crawl_lecture(*, course, lecture):
            # lecture videos
            resp = sess.get(URL_LECTURE_1(course['id'], lecture['id']))
            d = resp.json()

            for _ in d['linked']['onDemandVideos.v1']:
                url_subtitle = _['subtitles'].get('en')
                if url_subtitle is not None:
                    url_subtitle = URL_ROOT + url_subtitle

                url_video = None
                for reso in ['720p', '540p', '360p']:
                    url_video = _['sources']['byResolution'].get(reso)
                    if url_video is not None:
                        break

                assert url_video is not None

                url_video = url_video['mp4VideoUrl']
                lecture['videos'].append(Video(url_video=url_video, url_subtitle=url_subtitle))

            # lecture assets
            resp = sess.get(URL_LECTURE_2(course['id'], lecture['id']))
            d = resp.json()

            assetIDs = []
            for _ in d['linked']['openCourseAssets.v1']:
                typeName = _['typeName']
                if typeName == 'asset':
                    assetIDs.append(_['definition']['assetId'])
            assets = crawl_assets(assetIDs)
            lecture['assets'] = assets

        @ts.register_task(
            priority=PRIO_COURSE_MATERIAL, ttl=3,
            format_kwargs=lambda _: format_dict({'course': _['course']['slug'],
                                                 'supplement': _['supplement']['slug']})
        )
        def crawl_supplement(course, supplement):
            resp = sess.get(URL_SUPPLEMENT(course['id'], supplement['id']))
            d = resp.json()

            for _ in d['linked']['openCourseAssets.v1']:
                typeName = _['typeName']
                if typeName == 'cml':
                    cml = CML(_['definition']['value'])
                    assetIDs = cml.get_assetIDs()
                    assets = crawl_assets(assetIDs)
                    html = cml.to_html(assets=assets)

                    supplement['items'].append(CourseMaterialSupplementItemCML(html=html, assets=assets))

        def crawl_assets(ids):
            if len(ids) == 0:
                return []

            resp = sess.get(URL_ASSET(ids))
            d = resp.json()

            assets = []
            for _ in d['elements']:
                id_ = _['id']
                url = _['url']['url']
                name = _asset_name(_['name'], _['fileExtension'])

                assets.append(Asset(id_=id_, url=url, name=name))

            assert len(assets) == len(ids)
            return assets

        def _asset_name(name, fileExtension):
            fileExtension = '.' + fileExtension
            if not name.endswith(fileExtension):
                name += fileExtension
            return name

    def crawl(self, *, slug, isSpec):
        self.login()
        if isSpec:
            res = Spec(slug=slug)
            self.crawl_spec(spec=res)
        else:
            res = Course(slug=slug)
            self.crawl_course(course=res)
        failures = self._ts.wait()

        assert len(failures) == 0
        return res
