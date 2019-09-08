import pickle
import os
import logging

from http.cookiejar import CookieJar, MozillaCookieJar

from .define import *

from .lib.misc import format_dict
from .markup import CML

PRIO_SPEC = 'A'
PRIO_COURSE = 'B'
PRIO_COURSE_MATERIAL = 'C'


class Crawler:
    def __init__(self, *, ts, sess, cookies):
        self._ts = ts
        self._loggedin = False

        def attach(func):
            setattr(self, func.__name__, func)
            return func

        @attach
        def login():
            if isinstance(cookies, CookieJar):
                cj = cookies
            else:
                cj = MozillaCookieJar()
                cj.load(cookies)

            sess.cookies = cj
            self._loggedin = True

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
            format_kwargs=lambda _: format_dict({'cource': _['course']['slug']})
        )
        def crawl_course(*, course):
            resp = sess.get(URL_COURSE_1(course['slug']))
            d = resp.json()

            _ = d['elements'][0]
            course['name'] = _['name']
            course['id'] = _['id']

            assert course['slug'] == _['slug']

            # ------

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
                elif typeName in ['exam', 'quiz', 'phasedPeer']:
                    pass
                else:
                    logging.warning('[crawl_course] unknown typeName=%s\n%s' % (typeName, _))

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

            # ------

            crawl_course_references(course=course)

            for module in course['modules']:
                for lesson in module['lessons']:
                    for item in lesson['items']:
                        if item['type'] == 'Lecture':
                            crawl_lecture(course=course, lecture=item)
                        elif item['type'] == 'Supplement':
                            crawl_supplement(course=course, supplement=item)

        def _crawl_course_ref(course, id_ref=None):
            if not id_ref:
                resp = sess.get(URL_COURSE_REFERENCES(course['id']))
            else:
                resp = sess.get(URL_COURSE_REFERENCE(course['id'], id_ref))

            d = resp.json()

            itemId2ref = {}
            for _ in d['elements']:
                ref = CourseReference(id_=_['shortId'], name=_['name'], slug=_['slug'])
                course['references'].append(ref)

                itemId = _['content']['org.coursera.ondemand.reference.AssetReferenceContent']['assetId']
                itemId2ref[itemId] = ref

            for _ in d['linked']['openCourseAssets.v1']:
                typeName = _['typeName']
                if typeName == 'cml':
                    cml = CML(_['definition']['value'])
                    assets, assetIDs, refids = cml.get_resources()
                    assets += crawl_assets(assetIDs)
                    html = cml.to_html(assets=assets)

                    itemId2ref[_['id']]['item'] = CourseMaterialSupplementItemCML(html=html, assets=assets)

                    for refid in refids:
                        crawl_course_reference(course=course, id_ref=refid)
                else:
                    logging.warning("[_crawl_course_ref] unknown typeName=%s\n%s" % (typeName, _))

        @ts.register_task(
            priority=PRIO_COURSE_MATERIAL, ttl=3,
            format_kwargs=lambda _: format_dict({'cource': _['course']['slug']})
        )
        def crawl_course_references(*, course):
            _crawl_course_ref(course)

        @ts.register_task(
            priority=PRIO_COURSE_MATERIAL, ttl=3,
            format_kwargs=lambda _: format_dict({'cource': _['course']['slug']})
        )
        def crawl_course_reference(*, course, id_ref):
            for ref in course['references']:
                if id_ref == ref['id']:
                    return
            _crawl_course_ref(course, id_ref)

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

                _ = _['sources']['byResolution']
                url_video = _[sorted(_.keys())[-1]]  # choose the video with highest resolution
                url_video = url_video['mp4VideoUrl']

                lecture['videos'].append(Video(url_video=url_video, url_subtitle=url_subtitle))

            # lecture assets
            resp = sess.get(URL_LECTURE_2(course['id'], lecture['id']))
            d = resp.json()

            assets = []
            assetIDs = []
            for _ in d['linked']['openCourseAssets.v1']:
                typeName = _['typeName']
                if typeName == 'asset':
                    assetIDs.append(_['definition']['assetId'])
                elif typeName == 'url':
                    assets.append(Asset(id_=_['id'], url=_['definition']['url'], name=_['definition']['name']))
                else:
                    logging.warning("[crawl_lecture] unknown typeName=%s\n%s" % (typeName, _))

            assets += crawl_assets(assetIDs)
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
                    assets, assetIDs, refids = cml.get_resources()
                    assets += crawl_assets(assetIDs)
                    html = cml.to_html(assets=assets)

                    supplement['items'].append(CourseMaterialSupplementItemCML(html=html, assets=assets))

                    for refid in refids:
                        crawl_course_reference(course=course, id_ref=refid)
                else:
                    logging.warning("[crawl_supplement] unknown typeName=%s\n%s" % (typeName, _))

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
        if not self._loggedin:
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
