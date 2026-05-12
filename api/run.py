"""校园跑功能模块

映射 Java SchoolApi + 跑步服务 RunningServiceImpl 的核心逻辑：
  - 跑步标准 / 信息 / 记录 / 轨迹
  - 提交跑步记录（v1 旧版 / v2 新版，v2 匹配 Java 端完整字段）
  - 排名 / 首页排名
"""
from . import client
from .context import ctx


def get_run_info() -> dict:
    """获取当前学生跑步总览"""
    return client.get("v1/unirun/query/student/run/info")


def get_run_standard(school_id: int = None) -> dict:
    """获取跑步标准（无参则自动用当前学校）"""
    params = {}
    if school_id:
        params["schoolId"] = school_id
    elif ctx.user.schoolId:
        params["schoolId"] = ctx.user.schoolId
    return client.get("v1/unirun/query/runStandard", params)


def get_school_area(school_id: int = None) -> dict:
    """获取学校跑步区域边界（学校电子围栏）"""
    sid = school_id or ctx.user.schoolId
    return client.get("v1/unirun/querySchoolBound", {"schoolId": sid})


def get_run_records(page: int = 1, size: int = 10) -> dict:
    """获取跑步记录列表"""
    return client.get("v1/unirun/query/run/record", {"pageNum": page, "pageSize": size})


def get_run_records_by_user(user_id: int = None, year_semester: int = None,
                            page: int = 1, size: int = 10) -> dict:
    """按用户和学期筛选跑步记录"""
    params = {"pageNum": page, "pageSize": size}
    if user_id is not None:
        params["userId"] = user_id
    elif ctx.user.userId:
        params["userId"] = ctx.user.userId
    if year_semester is not None:
        params["yearSemester"] = year_semester
    return client.get("v1/unirun/query/run/record", params)


def get_run_semester_info(user_id: int = None, year_semester: str = None) -> dict:
    """获取学期跑步统计"""
    params = {}
    if user_id is not None:
        params["userId"] = user_id
    elif ctx.user.userId:
        params["userId"] = ctx.user.userId
    if year_semester is not None:
        params["yearSemester"] = year_semester
    return client.get("v1/unirun/query/runInfo", params)


def get_once_run_record(record_id: int, student_id: int = None) -> dict:
    """获取单次跑步详情（含轨迹点）"""
    sid = student_id or ctx.user.studentId
    return client.get("v1/unirun/query/student/record/info", {
        "recordId": record_id, "studentId": sid
    })


def get_record_track(record_id: int) -> dict:
    """获取跑步轨迹串"""
    return client.get("v1/unirun/query/student/record/track", {"recordId": record_id})


def start_run(student_id: int = None) -> dict:
    """开始跑步（服务端记录开始）"""
    sid = student_id or ctx.user.studentId
    return client.get("v1/push/startRun", {"studentId": sid})


def save_run_record(user_id: int = None, distance: int = 0, time: int = 0,
                    track_points: str = "", inner_school: str = "1",
                    year_semester: int = None) -> dict:
    """提交跑步记录 — v1 旧版接口

    对应 Java SaveRecordRequestBody
    """
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
    """提交跑步记录 — v2 新版接口（匹配 Java StudentRunRecordRequestBody）

    参数说明：
      distance_time_status: "1"=按距离+时间,"0"=仅距离
      vocal_status: 声纹验证状态 "0"/"1"
      again_run_status: 是否二次跑步 "0"/"1"
    """
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
    """获取学期排名（distance / count）"""
    return client.get("v1/unirun/querySchoolYearSemesterOrder", {"orderType": order_type})


def get_home_rank() -> dict:
    """获取首页排名（男/女榜）"""
    return client.get("v1/unirun/queryStudentRunOrder")


def get_banner_list(school_id: int = None) -> dict:
    """获取学校横幅"""
    sid = school_id or ctx.user.schoolId
    return client.get("v1/banner/getAllBannerBySchoolId", {"schoolId": sid})


def get_sports_score() -> dict:
    """获取体育成绩"""
    return client.get("v1/sports/class/getStudentSportsScoreDetail")


def get_semester_detail() -> dict:
    """获取学期详情"""
    return client.get("v1/sports/class/student/semester/detail")


def get_semester_score() -> dict:
    """获取学期扣分"""
    return client.get("v1/sports/class/student/semester/score")
