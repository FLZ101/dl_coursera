import json

from .lib.MyDict import MyDict

URL_ROOT = 'https://www.coursera.org'


def URL_LOGIN(csrf3_token):
    return URL_ROOT + '/api/login/v3Ssr?csrf3-token={}'.format(csrf3_token)


def URL_SPEC(slug):
    return URL_ROOT + '/api/onDemandSpecializations.v1?q=slug&slug={}&fields=courseIds,interchangeableCourseIds,launchedAt,logo,memberships,metadata,partnerIds,premiumExperienceVariant,onDemandSpecializationMemberships.v1(suggestedSessionSchedule),onDemandSpecializationSuggestedSchedule.v1(suggestedSessions),partners.v1(homeLink,name),courses.v1(courseProgress,description,membershipIds,startDate,v2Details,vcMembershipIds),v2Details.v1(onDemandSessions,plannedLaunchDate),memberships.v1(grade,vcMembershipId),vcMemberships.v1(certificateCodeWithGrade)&includes=courseIds,memberships,partnerIds,onDemandSpecializationMemberships.v1(suggestedSessionSchedule),courses.v1(courseProgress,membershipIds,v2Details,vcMembershipIds),v2Details.v1(onDemandSessions)'.format(slug)


def URL_COURSE_1(slug):
    return URL_ROOT + '/api/onDemandCourses.v1?q=slug&slug={}&includes=instructorIds%2CpartnerIds%2C_links&fields=brandingImage%2CcertificatePurchaseEnabledAt%2Cpartners.v1(squareLogo%2CrectangularLogo)%2Cinstructors.v1(fullName)%2CoverridePartnerLogos%2CsessionsEnabledAt%2CdomainTypes%2CpremiumExperienceVariant%2CisRestrictedMembership'.format(slug)


def URL_COURSE_2(slug):
    return URL_ROOT + '/api/onDemandCourseMaterials.v2/?q=slug&slug={}&includes=modules%2Clessons%2CpassableItemGroups%2CpassableItemGroupChoices%2CpassableLessonElements%2Citems%2Ctracks%2CgradePolicy&fields=moduleIds%2ConDemandCourseMaterialModules.v1(name%2Cslug%2Cdescription%2CtimeCommitment%2ClessonIds%2Coptional%2ClearningObjectives)%2ConDemandCourseMaterialLessons.v1(name%2Cslug%2CtimeCommitment%2CelementIds%2Coptional%2CtrackId)%2ConDemandCourseMaterialPassableItemGroups.v1(requiredPassedCount%2CpassableItemGroupChoiceIds%2CtrackId)%2ConDemandCourseMaterialPassableItemGroupChoices.v1(name%2Cdescription%2CitemIds)%2ConDemandCourseMaterialPassableLessonElements.v1(gradingWeight%2CisRequiredForPassing)%2ConDemandCourseMaterialItems.v2(name%2Cslug%2CtimeCommitment%2CcontentSummary%2CisLocked%2ClockableByItem%2CitemLockedReasonCode%2CtrackId%2ClockedStatus%2CitemLockSummary)%2ConDemandCourseMaterialTracks.v1(passablesCount)&showLockedItems=true'.format(slug)


def URL_LECTURE_1(id_course, id_lecture):
    return URL_ROOT + '/api/onDemandLectureVideos.v1/{}~{}?includes=video&fields=onDemandVideos.v1(sources%2Csubtitles%2CsubtitlesVtt%2CsubtitlesTxt)'.format(id_course, id_lecture)


def URL_LECTURE_2(id_course, id_lecture):
    return URL_ROOT + '/api/onDemandLectureAssets.v1/{}~{}/?includes=openCourseAssets'.format(id_course, id_lecture)


def URL_SUPPLEMENT(id_course, id_supplement):
    return URL_ROOT + '/api/onDemandSupplements.v1/{}~{}?includes=asset&fields=openCourseAssets.v1(typeName)%2CopenCourseAssets.v1(definition)'.format(id_course, id_supplement)


def URL_ASSET(ids):
    return URL_ROOT + '/api/assets.v1?ids={}&fields=audioSourceUrls%2C+videoSourceUrls%2C+videoThumbnailUrls%2C+fileExtension%2C+tags'.format(','.join(ids))


class Spec(MyDict):
    def __init__(self, *, id_=None, name=None, slug=None):
        super().__init__()

        self['type'] = 'Spec'
        self['id'] = id_
        self['name'] = name
        self['slug'] = slug
        self['courses'] = []


class Course(MyDict):
    def __init__(self, *, id_=None, name=None, slug=None):
        super().__init__()

        self['type'] = 'Course'
        self['id'] = id_
        self['name'] = name
        self['slug'] = slug
        self['modules'] = []


class CourseMaterialModule(MyDict):
    def __init__(self, *, id_=None, name=None, slug=None):
        super().__init__()

        self['type'] = 'Module'
        self['id'] = id_
        self['name'] = name
        self['slug'] = slug
        self['lessons'] = []


class CourseMaterialLesson(MyDict):
    def __init__(self, *, id_=None, name=None, slug=None):
        super().__init__()

        self['type'] = 'Lesson'
        self['id'] = id_
        self['name'] = name
        self['slug'] = slug
        self['items'] = []


class CourseMaterialLecture(MyDict):
    def __init__(self, *, id_=None, name=None, slug=None):
        super().__init__()

        self['type'] = 'Lecture'
        self['id'] = id_
        self['name'] = name
        self['slug'] = slug
        self['videos'] = []
        self['assets'] = []


class CourseMaterialSupplement(MyDict):
    def __init__(self, *, id_=None, name=None, slug=None):
        super().__init__()

        self['type'] = 'Supplement'
        self['id'] = id_
        self['name'] = name
        self['slug'] = slug
        self['items'] = []


class CourseMaterialSupplementItem(MyDict):
    pass


class CourseMaterialSupplementItemCML(CourseMaterialSupplementItem):
    def __init__(self, *, html, assets):
        super().__init__()

        self['type'] = 'CML'
        self['html'] = html
        self['assets'] = assets


class CourseMaterialNotebook(MyDict):
    def __init__(self, *, id_=None, name=None, slug=None):
        super().__init__()

        self['type'] = 'Notebook'
        self['id'] = id_
        self['name'] = name
        self['slug'] = slug


class Video(MyDict):
    def __init__(self, url_video, url_subtitle=None):
        super().__init__()

        self['url_video'] = url_video
        if url_subtitle is not None:
            self['url_subtitle'] = url_subtitle


class Asset(MyDict):
    def __init__(self, id_, url, name):
        super().__init__()

        self['id'] = id_
        self['url'] = url
        self['name'] = name
