from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class OauthToken:
    token: str = ""
    refreshToken: str = ""


@dataclass
class User:
    userId: int = 0
    studentId: int = 0
    schoolId: int = 0
    studentName: str = ""
    schoolName: str = ""
    gender: str = ""
    oauthToken: Optional[OauthToken] = None
    classId: int = 0
    className: str = ""
    collegeCode: str = ""
    collegeName: str = ""
    majorCode: str = ""
    majorName: str = ""
    registerCode: str = ""
    startSchool: int = 0
    studentClass: int = 0
    userVerifyStatus: str = ""
    birthday: str = ""
    idCardNo: str = ""
    nationCode: str = ""
    studentSource: str = ""
    addrDetail: str = ""
    mark: int = 0
    grade: int = 0
    gradeName: str = ""


@dataclass
class RunStandard:
    standardId: Optional[int] = None
    schoolId: Optional[int] = None
    boyOnceTimeMin: Optional[int] = None
    boyOnceTimeMax: Optional[int] = None
    boyOnceDistanceMin: Optional[int] = None
    boyOnceDistanceMax: Optional[int] = None
    boyAllRunDistance: Optional[int] = None
    boyAllRunTime: Optional[int] = None
    girlOnceTimeMin: Optional[int] = None
    girlOnceTimeMax: Optional[int] = None
    girlOnceDistanceMin: Optional[int] = None
    girlOnceDistanceMax: Optional[int] = None
    girlAllRunDistance: Optional[int] = None
    girlAllRunTime: Optional[int] = None
    firstSemesterDateStart: Optional[str] = None
    firstSemesterDateEnd: Optional[str] = None
    secondSemesterDateStart: Optional[str] = None
    secondSemesterDateEnd: Optional[str] = None
    vocalVerifyTime: Optional[int] = None
    instanceSemester: Optional[str] = None
    semesterYear: Optional[str] = None
    boyRunSpeed: Optional[int] = None
    girlRunSpeed: Optional[int] = None
    boyMaxSpeed: Optional[int] = None
    boyMinSpeed: Optional[int] = None
    girlMaxSpeed: Optional[int] = None
    girlMinSpeed: Optional[int] = None
    overSpeedWarn: Optional[str] = None
    vocalType: Optional[str] = None
    vocalStartTime: Optional[str] = None
    vocalEndTime: Optional[str] = None
    effectiveRangeType: Optional[str] = None


@dataclass
class StudentRunAll:
    runValidDay: int = 0
    runValidDistance: int = 0
    speed: int = 0
    showSpeed: str = ""


@dataclass
class SemesterRun:
    userId: int = 0
    studentId: int = 0
    schoolId: int = 0
    semesterId: int = 0
    yearSemester: int = 0
    runDay: int = 0
    runDistance: int = 0
    runCount: int = 0
    runCalorie: int = 0
    runValidDay: int = 0
    runValidDistance: int = 0
    runValidCount: int = 0
    runValidCalorie: int = 0
    createTime: str = ""
    infoStatus: str = ""


@dataclass
class RunRecord:
    recordId: int = 0
    userId: int = 0
    studentId: int = 0
    schoolId: int = 0
    yearSemester: int = 0
    recordDate: str = ""
    recordMonth: str = ""
    runDistance: int = 0
    runValidDistance: int = 0
    runTime: int = 0
    runValidTime: int = 0
    runSpeed: int = 0
    runCalorie: int = 0
    runValidCalorie: int = 0
    vocalStatus: str = ""
    runStatus: str = ""
    defeatedInfo: str = ""
    createTime: str = ""
    infoStatus: str = ""
    runSpeedWarn: str = ""
    defeatStudentRatio: int = 0
    suspectedStatus: str = ""
    rangeStatus: str = ""


@dataclass
class RunResult:
    recordId: Optional[int] = None
    resultStatus: str = ""
    resultDesc: str = ""
    overSpeedWarn: str = ""
    warnContent: str = ""


@dataclass
class RunRecordInfo:
    recordId: Optional[int] = None
    userId: Optional[int] = None
    studentId: Optional[int] = None
    yearSemester: Optional[int] = None
    recordDate: str = ""
    recordMonth: str = ""
    runDistance: Optional[int] = None
    runValidDistance: Optional[int] = None
    runTime: Optional[int] = None
    runValidTime: Optional[int] = None
    runSpeed: Optional[int] = None
    runCalorie: Optional[int] = None
    runValidCalorie: Optional[int] = None
    runStatus: str = ""
    runSpeedWarn: str = ""
    vocalStatus: str = ""
    defeatedInfo: str = ""
    defeatStudentRatio: Optional[int] = None
    createTime: str = ""
    infoStatus: str = ""


@dataclass
class RunRecordResult:
    recored: Optional[RunRecordInfo] = None
    studentName: str = ""
    trackPoint: str = ""


@dataclass
class SchoolBound:
    siteBound: str = ""
    siteName: str = ""
    boundCenter: str = ""


@dataclass
class RankList:
    studentId: int = 0
    studentName: str = ""
    majorName: str = ""
    startSchool: int = 0
    studentClass: int = 0
    runValidCount: int = 0
    runDistance: int = 0


@dataclass
class Rank:
    studentId: int = 0
    orderIndex: Optional[int] = None
    inOrder: str = ""
    runValidCount: Optional[int] = None
    runDistance: Optional[int] = None
    orderList: list = field(default_factory=list)


@dataclass
class HomeRank:
    studentId: int = 0
    orderIndex: Optional[int] = None
    inOrder: str = ""
    runValidCount: Optional[int] = None
    runDistance: Optional[int] = None
    yearSemester: Optional[int] = None
    boyList: list = field(default_factory=list)
    girlList: list = field(default_factory=list)


@dataclass
class ClubProject:
    itemId: int = 0
    itemName: str = ""
    joinNum: int = 0


@dataclass
class ClubActivity2:
    clubActivityId: int = 0
    activityName: str = ""
    addressDetail: str = ""
    clubIntroduction: str = ""
    startTime: str = ""
    endTime: str = ""
    teacherName: str = ""
    maxStudent: int = 0
    signInStudent: int = 0
    signStatus: str = ""
    cancelSign: str = ""
    fullActivity: str = ""
    optionStatus: str = ""


@dataclass
class MyClubActivity2:
    clubActivityId: int = 0
    activityName: str = ""
    activityStatus: str = ""
    addressDetail: str = ""
    clubIntroduction: str = ""
    configurationTimeId: int = 0
    signInStudent: int = 0
    maxStudent: int = 0
    teacherName: str = ""
    startTime: str = ""
    endTime: str = ""
    mmdd: str = ""
    nextClubActivityId: Optional[int] = None
    nextStartTime: str = ""
    nextEndTime: str = ""
    nextMmdd: str = ""
    nextSignInStudent: int = 0
    nextMaxStudent: int = 0
    nextHaveActivity: str = ""
    currentActivity: str = ""
    cancelSign: str = ""
    optionStatus: str = ""
    signStatus: str = ""
    clubType: str = ""
    yearSemester: str = ""
    signUpId: Optional[int] = None
    activityItemId: Optional[int] = None


@dataclass
class JoinClubResult:
    status: str = ""
    message: str = ""


@dataclass
class ClubRecord:
    configurationId: int = 0
    activityName: str = ""
    teacherName: str = ""
    weekDay: int = 0
    yymmdd: str = ""
    startTime: str = ""
    endTime: str = ""
    signStatus: str = ""


@dataclass
class SignInTf:
    signStatus: str = ""
    activityId: Optional[int] = None
    longitude: Optional[str] = None
    latitude: Optional[str] = None
    address: Optional[str] = None
    signInStatus: Optional[str] = None
    signBackStatus: Optional[str] = None
    startTime: Optional[str] = None
    endTime: Optional[str] = None
    signInTime: Optional[str] = None
    activityType: Optional[str] = None
    continueTime: Optional[int] = None
    signBackLimitTime: Optional[int] = None
    activityName: Optional[str] = None


@dataclass
class HomeClub:
    clubActivityId: str = ""
    activityItemId: str = ""
    itemName: str = ""
    activityName: str = ""
    startTime: str = ""
    endTime: str = ""
    addressDetail: str = ""
    maxStudent: str = ""
    applyStudentCount: str = ""


@dataclass
class ClubBanner:
    soupId: int = 0
    soupText: str = ""
    soupUrl: str = ""
    infoStatus: str = ""
    createTime: str = ""


@dataclass
class SemesterClubActivityVO:
    configurationId: int = 0
    activityName: str = ""
    addressDetail: str = ""
    clubIntroduction: str = ""
    teacherName: str = ""
    teacherId: int = 0
    studentNum: int = 0
    joinStudentNum: int = 0
    joinStatus: str = ""
    weekDay: str = ""
    startDay: str = ""
    endDay: str = ""
    startTime: str = ""
    endTime: str = ""


def dict_to_dataclass(cls, data: dict):
    if data is None:
        return None
    fields = {f.name for f in cls.__dataclass_fields__.values()}
    filtered = {k: v for k, v in data.items() if k in fields}
    return cls(**filtered)


def dict_to_dataclass_list(cls, data: list):
    if data is None:
        return []
    return [dict_to_dataclass(cls, item) for item in data]
