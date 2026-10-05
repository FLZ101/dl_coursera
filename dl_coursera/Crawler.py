import os
import logging
import base64
import html as html_lib

from http.cookiejar import MozillaCookieJar

import requests

from .define import *

from .lib.misc import format_dict, TmpFile
from .markup import CML

PRIO_SPEC = 'A'
PRIO_COURSE = 'B'
PRIO_COURSE_MATERIAL = 'C'

QUIZ_TYPE_NAMES = [
    'staffGraded',
    'ungradedAssignment',
    'quiz',
    'assessOpenSinglePage',
]

URL_GRAPHQL_GATEWAY = URL_ROOT + '/graphql-gateway'

GRAPHQL_START_ATTEMPT = r'''
mutation Submission_StartAttempt($courseId: ID!, $itemId: ID!) {
  Submission_StartAttempt(input: {courseId: $courseId, itemId: $itemId}) {
    ... on Submission_StartAttemptSuccess {
      submissionState {
        assignment {
          id
          __typename
        }
        __typename
      }
      __typename
    }
    ... on Submission_StartAttemptFailure {
      errors {
        errorCode
        __typename
      }
      __typename
    }
    __typename
  }
}
'''

GRAPHQL_QUERY_QUIZ_STATE = r'''
fragment CmlFields on CmlContent {
  cmlValue
  __typename
}

fragment HtmlFields on Submission_HtmlContent {
  value
  __typename
}

fragment ChoiceQuestion on Submission_MultipleChoiceQuestion {
  partId: id
  questionSchema {
    prompt {
      ...CmlFields
      ...HtmlFields
      __typename
    }
    options {
      optionId: id
      display {
        ...CmlFields
        ...HtmlFields
        __typename
      }
      __typename
    }
    __typename
  }
  __typename
}

fragment CheckboxQuestion on Submission_CheckboxQuestion {
  partId: id
  questionSchema {
    prompt {
      ...CmlFields
      ...HtmlFields
      __typename
    }
    options {
      optionId: id
      display {
        ...CmlFields
        ...HtmlFields
        __typename
      }
      __typename
    }
    __typename
  }
  __typename
}

fragment CheckboxReflectQuestion on Submission_CheckboxReflectQuestion {
  partId: id
  questionSchema {
    prompt {
      ...CmlFields
      ...HtmlFields
      __typename
    }
    options {
      optionId: id
      display {
        ...CmlFields
        ...HtmlFields
        __typename
      }
      __typename
    }
    __typename
  }
  __typename
}

fragment ReflectChoiceQuestion on Submission_MultipleChoiceReflectQuestion {
  partId: id
  questionSchema {
    prompt {
      ...CmlFields
      ...HtmlFields
      __typename
    }
    options {
      optionId: id
      display {
        ...CmlFields
        ...HtmlFields
        __typename
      }
      __typename
    }
    __typename
  }
  __typename
}

fragment TextQuestion on Submission_PlainTextQuestion {
  partId: id
  questionSchema {
    prompt {
      ...CmlFields
      ...HtmlFields
      __typename
    }
    __typename
  }
  __typename
}

fragment RegexQuestion on Submission_RegexQuestion {
  partId: id
  questionSchema {
    prompt {
      ...CmlFields
      ...HtmlFields
      __typename
    }
    __typename
  }
  __typename
}

fragment ExactTextQuestion on Submission_TextExactMatchQuestion {
  partId: id
  questionSchema {
    prompt {
      ...CmlFields
      ...HtmlFields
      __typename
    }
    __typename
  }
  __typename
}

fragment ReflectTextQuestion on Submission_TextReflectQuestion {
  partId: id
  questionSchema {
    prompt {
      ...CmlFields
      ...HtmlFields
      __typename
    }
    __typename
  }
  __typename
}

fragment RichTextQuestion on Submission_RichTextQuestion {
  partId: id
  questionSchema {
    prompt {
      ...CmlFields
      ...HtmlFields
      __typename
    }
    __typename
  }
  __typename
}

fragment NumericQuestion on Submission_NumericQuestion {
  partId: id
  questionSchema {
    prompt {
      ...CmlFields
      ...HtmlFields
      __typename
    }
    __typename
  }
  __typename
}

fragment UrlQuestion on Submission_UrlQuestion {
  partId: id
  questionSchema {
    prompt {
      ...CmlFields
      ...HtmlFields
      __typename
    }
    __typename
  }
  __typename
}

fragment MathQuestion on Submission_MathQuestion {
  partId: id
  questionSchema {
    prompt {
      ...CmlFields
      ...HtmlFields
      __typename
    }
    __typename
  }
  __typename
}

fragment CodeQuestion on Submission_CodeExpressionQuestion {
  partId: id
  questionSchema {
    prompt {
      ...CmlFields
      ...HtmlFields
      __typename
    }
    __typename
  }
  __typename
}

fragment FileQuestion on Submission_FileUploadQuestion {
  partId: id
  questionSchema {
    prompt {
      ...CmlFields
      ...HtmlFields
      __typename
    }
    __typename
  }
  __typename
}

fragment WidgetQuestion on Submission_WidgetQuestion {
  partId: id
  questionSchema {
    prompt {
      ...CmlFields
      ...HtmlFields
      __typename
    }
    __typename
  }
  __typename
}

fragment FillableBlanksQuestion on Submission_MultipleFillableBlanksQuestion {
  partId: id
  questionSchema {
    prompt {
      ...CmlFields
      ...HtmlFields
      __typename
    }
    __typename
  }
  __typename
}

fragment OffPlatformQuestion on Submission_OffPlatformQuestion {
  partId: id
  questionSchema {
    prompt {
      ...CmlFields
      ...HtmlFields
      __typename
    }
    __typename
  }
  __typename
}

fragment TextBlockPart on Submission_TextBlock {
  partId: id
  title
  body {
    ...CmlFields
    __typename
  }
  __typename
}

query QueryState($courseId: ID!, $itemId: ID!) {
  SubmissionState {
    queryState(courseId: $courseId, itemId: $itemId) {
      __typename
      ... on Submission_QueryStateFailure {
        errors {
          errorCode
          __typename
        }
        __typename
      }
      ... on Submission_SubmissionState {
        allowedAction
        attempts {
          inProgressAttempt {
            draft {
              id
              instructions {
                overview {
                  ...CmlFields
                  ...HtmlFields
                  __typename
                }
                __typename
              }
              parts {
                ...ChoiceQuestion
                ...CheckboxQuestion
                ...CheckboxReflectQuestion
                ...ReflectChoiceQuestion
                ...TextQuestion
                ...RegexQuestion
                ...ExactTextQuestion
                ...ReflectTextQuestion
                ...RichTextQuestion
                ...NumericQuestion
                ...UrlQuestion
                ...MathQuestion
                ...CodeQuestion
                ...FileQuestion
                ...WidgetQuestion
                ...FillableBlanksQuestion
                ...OffPlatformQuestion
                ...TextBlockPart
              }
              __typename
            }
            __typename
          }
          lastSubmission {
            submission {
              id
              instructions {
                overview {
                  ...CmlFields
                  ...HtmlFields
                  __typename
                }
                __typename
              }
              parts {
                ...ChoiceQuestion
                ...CheckboxQuestion
                ...CheckboxReflectQuestion
                ...ReflectChoiceQuestion
                ...TextQuestion
                ...RegexQuestion
                ...ExactTextQuestion
                ...ReflectTextQuestion
                ...RichTextQuestion
                ...NumericQuestion
                ...UrlQuestion
                ...MathQuestion
                ...CodeQuestion
                ...FileQuestion
                ...WidgetQuestion
                ...FillableBlanksQuestion
                ...OffPlatformQuestion
                ...TextBlockPart
              }
              __typename
            }
            __typename
          }
          __typename
        }
        __typename
      }
      __typename
    }
    __typename
  }
}
'''


def login(sess, cookies_file=None):
    if cookies_file is None:
        # the env should contain $(base64 -w 0 cookies.txt)
        cookies_base64 = os.environ.get('DL_COURSERA_COOKIES_BASE64')
        assert cookies_base64

        cookies = base64.standard_b64decode(cookies_base64)

        with TmpFile() as tmpfile:
            with open(tmpfile, 'wb') as ofs:
                ofs.write(cookies)

            cj = MozillaCookieJar()
            cj.load(tmpfile)
    else:
        cj = MozillaCookieJar()
        cj.load(cookies_file)

    sess.cookies.update(cj)


class Crawler:
    @staticmethod
    def _get(sess, url):
        resp = sess.get(url)
        d = resp.json()
        if 'errorCode' in d:
            raise BadResponseException(d)
        return d

    @staticmethod
    def _post(sess: requests.Session, url, json: dict = {}):
        resp = sess.post(url, json=json)
        d = resp.json()
        if 'errorCode' in d:
            raise BadResponseException(d)
        return d

    @staticmethod
    def _graphql(sess: requests.Session, operation, payload):
        resp = sess.post(URL_GRAPHQL_GATEWAY + '?opname=' + operation, json=payload)
        resp.raise_for_status()
        return resp.json()

    def __init__(
        self, *, ts, sess: requests.Session, cookies_file=None, include_quiz=False
    ):
        self._ts = ts
        self._sess = sess
        self._cookies_file = cookies_file
        self._include_quiz = include_quiz

        self._loggedin = False
        self._uid: str = None

        def attach(func):
            setattr(self, func.__name__, func)
            return func

        @attach
        @ts.register_task(
            priority=PRIO_SPEC,
            ttl=3,
            format_kwargs=lambda _: format_dict({'spec': _['spec']['slug']}),
        )
        def crawl_spec(*, spec):
            d = Crawler._get(sess, URL_SPEC(spec['slug']))
            if 'elements' not in d:
                raise SpecNotExistExcepton(spec['slug'])

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

            logging.info(
                'Courses of specialization %s: %s'
                % (spec['slug'], ', '.join([_['slug'] for _ in spec['courses']]))
            )

            for _ in spec['courses']:
                crawl_course(course=_)

        @attach
        @ts.register_task(
            priority=PRIO_COURSE,
            ttl=3,
            format_kwargs=lambda _: format_dict({'cource': _['course']['slug']}),
        )
        def crawl_course(*, course):
            d = Crawler._get(sess, URL_COURSE_1(course['slug']))
            if 'elements' not in d:
                raise CourseNotExistExcepton(course['slug'])

            _ = d['elements'][0]
            course['name'] = _['name']
            course['id'] = _['id']

            assert course['slug'] == _['slug']

            # ------

            d = Crawler._get(sess, URL_COURSE_2(course['slug']))['linked']

            id2item = {}
            for _ in d['onDemandCourseMaterialItems.v2']:
                typeName = _['contentSummary']['typeName']
                if typeName in [
                    'exam',
                    'phasedPeer',
                    'discussionPrompt',
                    'gradedProgramming',
                    'programming',
                    'ungradedLti',
                    'notebook',
                    'ungradedLab',
                ]:
                    continue

                if typeName not in ['lecture', 'supplement'] + QUIZ_TYPE_NAMES:
                    logging.warning(
                        '[crawl_course] unknown typeName=%s\n%s' % (typeName, _)
                    )
                    continue

                if _.get('isLocked'):
                    logging.info('[crawl_course] locked item: %s' % _)
                    continue

                if typeName == 'lecture':
                    id2item[_['id']] = CourseMaterialLecture(
                        id_=_['id'], name=_['name'], slug=_['slug']
                    )
                elif typeName == 'supplement':
                    id2item[_['id']] = CourseMaterialSupplement(
                        id_=_['id'], name=_['name'], slug=_['slug']
                    )
                elif typeName in QUIZ_TYPE_NAMES and self._include_quiz:
                    id2item[_['id']] = CourseMaterialQuiz(
                        id_=_['id'], name=_['name'], slug=_['slug']
                    )

            id2lesson = {}
            for _ in d['onDemandCourseMaterialLessons.v1']:
                lesson = CourseMaterialLesson(
                    id_=_['id'], name=_['name'], slug=_['slug']
                )
                for id_item in _['itemIds']:
                    item = id2item.get(id_item)
                    if item is not None:
                        lesson['items'].append(item)

                if len(lesson['items']) > 0:
                    id2lesson[lesson['id']] = lesson

            for _ in d['onDemandCourseMaterialModules.v1']:
                module = CourseMaterialModule(
                    id_=_['id'], name=_['name'], slug=_['slug']
                )

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
                        elif item['type'] == 'Quiz':
                            crawl_quiz(course=course, quiz=item)

        def _cook_cml_parts(course, cml: CML):
            assets, assetIDs, refids = cml.get_resources()
            assets += crawl_assets(assetIDs)
            html = cml.to_html(assets=assets)

            for refid in refids:
                crawl_course_reference(course=course, id_ref=refid)

            return html, assets

        def _cook_cml(course, cml: CML):
            html, assets = _cook_cml_parts(course, cml)
            return CourseMaterialSupplementItemCML(html=html, assets=assets)

        def _crawl_course_ref(course, id_ref=None):
            if not id_ref:
                d = Crawler._get(sess, URL_COURSE_REFERENCES(course['id']))
            else:
                d = Crawler._get(sess, URL_COURSE_REFERENCE(course['id'], id_ref))

            itemId2ref = {}
            for _ in d['elements']:
                ref = CourseReference(id_=_['shortId'], name=_['name'], slug=_['slug'])
                course['references'].append(ref)

                itemId = _['content'][
                    'org.coursera.ondemand.reference.AssetReferenceContent'
                ]['assetId']
                itemId2ref[itemId] = ref

            for _ in d['linked']['openCourseAssets.v1']:
                typeName = _['typeName']
                if typeName == 'cml':
                    cml = CML(_['definition']['value'])
                    itemId2ref[_['id']]['item'] = _cook_cml(course, cml)
                else:
                    logging.warning(
                        "[_crawl_course_ref] unknown typeName=%s\n%s" % (typeName, _)
                    )

        @ts.register_task(
            priority=PRIO_COURSE_MATERIAL,
            ttl=3,
            format_kwargs=lambda _: format_dict({'cource': _['course']['slug']}),
        )
        def crawl_course_references(*, course):
            _crawl_course_ref(course)

        @ts.register_task(
            priority=PRIO_COURSE_MATERIAL,
            ttl=3,
            format_kwargs=lambda _: format_dict(
                {'cource': _['course']['slug'], 'id_ref': _['id_ref']}
            ),
        )
        def crawl_course_reference(*, course, id_ref):
            for ref in course['references']:
                if id_ref == ref['id']:
                    return
            _crawl_course_ref(course, id_ref)

        @ts.register_task(
            priority=PRIO_COURSE_MATERIAL,
            ttl=3,
            format_kwargs=lambda _: format_dict(
                {'course': _['course']['slug'], 'lecture': _['lecture']['slug']}
            ),
        )
        def crawl_lecture(*, course, lecture):
            # lecture videos
            d = Crawler._get(sess, URL_LECTURE_1(course['id'], lecture['id']))

            for _ in d['linked']['onDemandVideos.v1']:
                subtitles = {}
                for lang, url_subtitle in (_['subtitles'] or {}).items():
                    if url_subtitle:
                        subtitles[lang] = URL_ROOT + url_subtitle

                _ = _['sources']['byResolution']
                # choose the video with highest resolution
                url_video = _[sorted(_.keys())[-1]]
                url_video = url_video['mp4VideoUrl']

                lecture['videos'].append(
                    Video(url_video=url_video, subtitles=subtitles)
                )

            # lecture assets
            d = Crawler._get(sess, URL_LECTURE_2(course['id'], lecture['id']))

            assets = []
            assetIDs = []
            for _ in d['linked']['openCourseAssets.v1']:
                typeName = _['typeName']
                if typeName == 'asset':
                    assetIDs.append(_['definition']['assetId'])
                elif typeName == 'url':
                    assets.append(
                        Asset(
                            id_=_['id'],
                            url=_['definition']['url'],
                            name=_['definition']['name'],
                        )
                    )
                else:
                    logging.warning(
                        "[crawl_lecture] unknown typeName=%s\n%s" % (typeName, _)
                    )

            assets += crawl_assets(assetIDs)
            lecture['assets'] = assets

        @ts.register_task(
            priority=PRIO_COURSE_MATERIAL,
            ttl=3,
            format_kwargs=lambda _: format_dict(
                {'course': _['course']['slug'], 'supplement': _['supplement']['slug']}
            ),
        )
        def crawl_supplement(course, supplement):
            d = Crawler._get(sess, URL_SUPPLEMENT(course['id'], supplement['id']))
            for _ in d['linked']['openCourseAssets.v1']:
                typeName = _['typeName']
                if typeName == 'cml':
                    cml = CML(_['definition']['value'])
                    supplement['items'].append(_cook_cml(course, cml))
                else:
                    logging.warning(
                        "[crawl_supplement] unknown typeName=%s\n%s" % (typeName, _)
                    )

        def _graphql_payload(operation, query, variables):
            return [
                {
                    'operationName': operation,
                    'variables': variables,
                    'query': query,
                }
            ]

        def _graphql_data(d):
            return d[0]['data']

        def _quiz_state(course, quiz):
            payload = _graphql_payload(
                'QueryState',
                GRAPHQL_QUERY_QUIZ_STATE,
                {'courseId': course['id'], 'itemId': quiz['id']},
            )
            d = Crawler._graphql(sess, 'QueryState', payload)
            return _graphql_data(d)['SubmissionState']['queryState']

        def _quiz_content_to_html(course, content):
            if not isinstance(content, dict):
                return '', []

            if content.get('cmlValue') is not None:
                cml = CML(content['cmlValue'])
                return _cook_cml_parts(course, cml)

            if content.get('value') is not None:
                return content['value'], []

            return '', []

        def _quiz_part_to_html(course, part):
            html = []
            assets = []

            schema = part.get('questionSchema') or {}
            type_name = part.get('__typename')

            prompt_html, prompt_assets = _quiz_content_to_html(
                course, schema.get('prompt')
            )
            if prompt_html:
                html.append('<div class="quiz-prompt">%s</div>' % prompt_html)
            assets += prompt_assets

            options = schema.get('options') or []
            if options:
                input_type = None
                if type_name in [
                    'Submission_CheckboxQuestion',
                    'Submission_CheckboxReflectQuestion',
                ]:
                    input_type = 'checkbox'
                elif type_name in [
                    'Submission_MultipleChoiceQuestion',
                    'Submission_MultipleChoiceReflectQuestion',
                ]:
                    input_type = 'radio'

                html.append('<ul class="quiz-options">')
                for option in options:
                    option_html, option_assets = _quiz_content_to_html(
                        course, option.get('display')
                    )
                    assets += option_assets

                    input_html = ''
                    if input_type is not None:
                        name = html_lib.escape(str(part.get('partId', 'quiz-question')))
                        attrs = 'type="%s" name="%s"' % (input_type, name)
                        input_html = '<input %s>' % attrs

                    html.append(
                        '<li>%s <div class="quiz-option-text">%s</div></li>'
                        % (input_html, option_html)
                    )
                html.append('</ul>')

            title = part.get('title')
            body = part.get('body')
            if title and body:
                body_html, body_assets = _quiz_content_to_html(course, body)
                assets += body_assets
                html.append('<h3>%s</h3>%s' % (title, body_html))

            return '\n'.join(html), assets

        def _quiz_draft_to_html(course, draft):
            html = []
            assets = []

            instructions = draft.get('instructions') or {}
            overview = instructions.get('overview')
            overview_html, overview_assets = _quiz_content_to_html(course, overview)
            if overview_html:
                html.append('<div class="quiz-instructions">%s</div>' % overview_html)
            assets += overview_assets

            for part in draft.get('parts', []):
                part_html, part_assets = _quiz_part_to_html(course, part)
                if part_html:
                    html.append('<div class="quiz-question">%s</div>' % part_html)
                assets += part_assets

            unique_assets = []
            seen = set()
            for asset in assets:
                if asset['id'] not in seen:
                    seen.add(asset['id'])
                    unique_assets.append(asset)

            return '\n'.join(html), unique_assets

        @ts.register_task(
            priority=PRIO_COURSE_MATERIAL,
            ttl=3,
            format_kwargs=lambda _: format_dict(
                {'course': _['course']['slug'], 'quiz': _['quiz']['slug']}
            ),
        )
        def crawl_quiz(*, course, quiz):
            # Coursera exposes quiz questions as part of an attempt draft.
            # If no draft exists yet, start an attempt so that QueryState can
            # return the question prompts and options.
            state = _quiz_state(course, quiz)
            if state.get('__typename') != 'Submission_SubmissionState':
                logging.warning('[crawl_quiz] failed to get quiz state: %s' % state)
                return

            attempts = state.get('attempts') or {}
            draft = None
            if attempts.get('inProgressAttempt'):
                draft = attempts['inProgressAttempt'].get('draft')
            elif attempts.get('lastSubmission'):
                draft = attempts['lastSubmission'].get('submission')

            if draft is None:
                start_payload = _graphql_payload(
                    'Submission_StartAttempt',
                    GRAPHQL_START_ATTEMPT,
                    {'courseId': course['id'], 'itemId': quiz['id']},
                )
                start_d = Crawler._graphql(
                    sess, 'Submission_StartAttempt', start_payload
                )
                start_result = _graphql_data(start_d)['Submission_StartAttempt']
                if start_result.get('__typename') != 'Submission_StartAttemptSuccess':
                    logging.warning(
                        '[crawl_quiz] failed to start quiz: %s' % start_result
                    )
                    return

                state = _quiz_state(course, quiz)
                attempts = state.get('attempts') or {}
                if attempts.get('inProgressAttempt'):
                    draft = attempts['inProgressAttempt'].get('draft')
                elif attempts.get('lastSubmission'):
                    draft = attempts['lastSubmission'].get('submission')

            if not draft:
                logging.warning('[crawl_quiz] no draft for quiz: %s' % quiz['slug'])
                return

            html, assets = _quiz_draft_to_html(course, draft)
            quiz['items'].append(
                CourseMaterialSupplementItemCML(html=html, assets=assets)
            )

        def crawl_assets(ids):
            if len(ids) == 0:
                return []

            d = Crawler._get(sess, URL_ASSET(ids))

            assets = []
            for _ in d['elements']:
                id_ = _['id']
                url = _['url']['url']
                name = _asset_name(_['name'], _['fileExtension'])
                assets.append(Asset(id_=id_, url=url, name=name))

            if len(assets) != len(ids):
                logging.warning(
                    '[crawl_assets] unexpected number of assets\n%s\n%s' % (ids, assets)
                )
            return assets

        def _asset_name(name, fileExtension):
            fileExtension = '.' + fileExtension
            if not name.endswith(fileExtension):
                name += fileExtension
            return name

    def login(self):
        if not self._loggedin:
            login(self._sess, self._cookies_file)
            self._loggedin = True

    def crawl(self, *, slug, is_spec):
        if not self._loggedin:
            self.login()

        if is_spec:
            res = Spec(slug=slug)
            self.crawl_spec(spec=res)
        else:
            res = Course(slug=slug)
            self.crawl_course(course=res)

        self._ts.wait()
        return res
