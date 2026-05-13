from . import client
from .context import ctx


def get_run_info() -> dict:
    return client.get("v1/unirun/query/student/run/info")


def get_run_standard(school_id: int = None) -> dict:
    params = {}
    if school_id:
        params["schoolId"] = school_id
    elif ctx.user.schoolId:
        params["schoolId"] = ctx.user.schoolId
    return client.get("v1/unirun/query/runStandard", params)


def get_school_area(school_id: int = None) -> dict:
    sid = school_id or ctx.user.schoolId
    return client.get("v1/unirun/querySchoolBound", {"schoolId": sid})


def get_run_records(page: int = 1, size: int = 10) -> dict:
    return client.get("v1/unirun/query/run/record", {"pageNum": page, "pageSize": size})


def get_run_records_by_user(user_id: int = None, year_semester: int = None,
                            page: int = 1, size: int = 10) -> dict:
    params = {"pageNum": page, "pageSize": size}
    if user_id is not None:
        params["userId"] = user_id
    elif ctx.user.userId:
        params["userId"] = ctx.user.userId
    if year_semester is not None:
        params["yearSemester"] = year_semester
    return client.get("v1/unirun/query/run/record", params)


def get_run_semester_info(user_id: int = None, year_semester: str = None) -> dict:
    params = {}
    if user_id is not None:
        params["userId"] = user_id
    elif ctx.user.userId:
        params["userId"] = ctx.user.userId
    if year_semester is not None:
        params["yearSemester"] = year_semester
    return client.get("v1/unirun/query/runInfo", params)


def get_once_run_record(record_id: int, student_id: int = None) -> dict:
    sid = student_id or ctx.user.studentId
    return client.get("v1/unirun/query/student/record/info", {
        "recordId": record_id, "studentId": sid
    })


def get_record_track(record_id: int) -> dict:
    return client.get("v1/unirun/query/student/record/track", {"recordId": record_id})


def start_run(student_id: int = None) -> dict:
    sid = student_id or ctx.user.studentId
    return client.get("v1/push/startRun", {"studentId": sid})


def save_run_record(user_id: int = None, distance: int = 0, time: int = 0,
                    track_points: str = "", inner_school: str = "1",
                    year_semester: int = None) -> dict:
    uid = user_id or ctx.user.userId
    ys = year_semester or 20261
    return client.post("v1/unirun/save/run/record", {
        "distanceTimeStatus": 0,
        "innerSchool": inner_school,
        "runDistance": distance,
        "runTime": time,
        "trackPoints": track_points,
        "userId": uid,
        "vocalStatus": "",
        "yearSemester": ys,
    })


def save_run_record_v2(user_id: int = None, distance: int = 0, time: int = 0,
                       track_points: str = "", reality_track: str = "",
                       inner_school: str = "1", year_semester: str = "20261",
                       record_date: str = "", again_run_status: str = "",
                       again_run_time: int = 0,
                       distance_time_status: str = "1",
                       vocal_status: str = "") -> dict:
    uid = user_id or ctx.user.userId
    return client.post("v1/unirun/save/run/record/new", {
        "againRunStatus": again_run_status,
        "againRunTime": again_run_time,
        "appVersions": "1.8.5",
        "brand": "Xiaomi",
        "mobileType": "Mi 10",
        "sysVersions": "12",
        "trackPoints": track_points,
        "distanceTimeStatus": distance_time_status,
        "innerSchool": inner_school,
        "runDistance": distance,
        "runTime": time,
        "userId": uid,
        "vocalStatus": vocal_status,
        "yearSemester": year_semester,
        "recordDate": record_date,
        "realityTrackPoints": reality_track,
    })


def get_rank(order_type: str = "distance") -> dict:
    return client.get("v1/unirun/querySchoolYearSemesterOrder", {"orderType": order_type})


def get_home_rank() -> dict:
    return client.get("v1/unirun/queryStudentRunOrder")


def get_banner_list(school_id: int = None) -> dict:
    sid = school_id or ctx.user.schoolId
    return client.get("v1/banner/getAllBannerBySchoolId", {"schoolId": sid})


def get_sports_score() -> dict:
    return client.get("v1/sports/class/getStudentSportsScoreDetail")


def get_semester_detail() -> dict:
    return client.get("v1/sports/class/student/semester/detail")


def get_semester_score() -> dict:
    return client.get("v1/sports/class/student/semester/score")
