from . import client
from .context import ctx


def get_club_projects(student_id: int = None, school_id: int = None) -> dict:
    params = {}
    if student_id is not None:
        params["studentId"] = student_id
    elif ctx.user.studentId:
        params["studentId"] = ctx.user.studentId
    if school_id is not None:
        params["schoolId"] = school_id
    elif ctx.user.schoolId:
        params["schoolId"] = ctx.user.schoolId
    return client.get("v1/clubactivity/getMyClubItemList", params)


def get_club_projects_by_type(student_id: int = None, school_id: int = None,
                              type_: int = None) -> dict:
    params = {}
    if student_id is not None:
        params["studentId"] = student_id
    elif ctx.user.studentId:
        params["studentId"] = ctx.user.studentId
    if school_id is not None:
        params["schoolId"] = school_id
    elif ctx.user.schoolId:
        params["schoolId"] = ctx.user.schoolId
    if type_ is not None:
        params["type"] = type_
    return client.get("v1/clubactivity/getMyClubItemList", params)


def get_activity_list(query_time: str = None, student_id: int = None,
                      school_id: int = None, activity_item_id: int = None,
                      page: int = 1, size: int = 15) -> dict:
    params = {"pageNo": page, "pageSize": size}
    if query_time:
        params["queryTime"] = query_time
    if student_id is not None:
        params["studentId"] = student_id
    elif ctx.user.studentId:
        params["studentId"] = ctx.user.studentId
    if school_id is not None:
        params["schoolId"] = school_id
    elif ctx.user.schoolId:
        params["schoolId"] = ctx.user.schoolId
    if activity_item_id is not None:
        params["activityItemId"] = activity_item_id
    return client.get("v1/clubactivity/queryActivityList", params)


def join_activity(student_id: int = None, activity_id: int = 0) -> dict:
    sid = student_id or ctx.user.studentId
    return client.get("v1/clubactivity/joinClubActivity", {
        "studentId": sid, "activityId": activity_id
    })


def cancel_activity(student_id: int = None, activity_id: int = 0) -> dict:
    sid = student_id or ctx.user.studentId
    return client.get("v1/clubactivity/cancelActivity", {
        "studentId": sid, "activityId": activity_id
    })


def get_my_activities(student_id: int = None, page: int = 1, size: int = 15) -> dict:
    sid = student_id or ctx.user.studentId
    return client.get("v1/clubactivity/queryMyActivityList", {
        "studentId": sid, "pageNo": page, "pageSize": size
    })


def get_club_records(student_id: int = None, page: int = 1, size: int = 10) -> dict:
    sid = student_id or ctx.user.studentId
    return client.get("v1/clubactivity/getStudentClubRecord", {
        "studentId": sid, "pageNo": page, "pageSize": size
    })


def get_club_banner(school_id: int = None) -> dict:
    sid = school_id or ctx.user.schoolId
    return client.get("v1/banner/querySchoolBannerChickenSoup", {"schoolId": sid})


def join_or_cancel_semester(config_id: int, type_: str) -> dict:
    return client.get("v1/clubactivity/joinOrCancelSchoolSemesterActivity", {
        "configurationId": config_id, "type": type_
    })


def get_semester_activities(week_day: str = None, activity_item_id: int = None,
                            page: int = 1, size: int = 15) -> dict:
    params = {"pageNo": page, "pageSize": size}
    if week_day:
        params["weekDay"] = week_day
    if activity_item_id is not None:
        params["activityItemId"] = activity_item_id
    return client.get("v1/clubactivity/querySemesterClubActivity", params)


def get_my_semester_activities() -> dict:
    return client.get("v1/clubactivity/queryMySemesterClubActivity")


def get_sign_in_tf(student_id: int = None) -> dict:
    sid = student_id or ctx.user.studentId
    return client.get("v1/clubactivity/getSignInTf", {"studentId": sid})


def sign_in_or_back(activity_id: int, latitude: str, longitude: str,
                    sign_type: str = "1", student_id: int = None) -> dict:
    sid = student_id or ctx.user.studentId
    return client.post("v1/clubactivity/signInOrSignBack", {
        "activityId": activity_id,
        "latitude": latitude,
        "longitude": longitude,
        "signType": sign_type,
        "studentId": sid,
    })


def sign_apply(activity_id: int, reason: str, apply_type: str = "1",
               latitude: str = "", longitude: str = "",
               pic1: str = "", pic2: str = "", pic3: str = "",
               student_id: int = None, school_id: int = None) -> dict:
    sid = student_id or ctx.user.studentId
    scid = school_id or ctx.user.schoolId
    return client.post("v1/clubactivity/signApply", {
        "activityId": activity_id,
        "applyType": apply_type,
        "latitude": latitude,
        "longitude": longitude,
        "pic1": pic1,
        "pic2": pic2,
        "pic3": pic3,
        "reason": reason,
        "schoolId": scid,
        "studentId": sid,
    })


def get_apply_introduce() -> dict:
    return client.get("v1/clubactivity/getApplyIntroduce")


def count_valid_sign_up(student_id: int = None) -> dict:
    params = {}
    if student_id is not None:
        params["studentId"] = student_id
    elif ctx.user.studentId:
        params["studentId"] = ctx.user.studentId
    return client.get("v1/clubactivity/countValidSignUp", params)


def add_advice(body: dict) -> dict:
    return client.post("v1/clubactivity/addAdvice", body)


def get_advice_types() -> dict:
    return client.get("v1/clubactivity/getAdviceTypeList")


def get_home_club() -> dict:
    return client.get("v1/clubactivity/querySchoolActivityTopThree")
