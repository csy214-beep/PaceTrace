"""俱乐部功能模块

映射 Java ClubService / ClubApi / SignInApi 的核心逻辑：
  - 项目列表 / 活动列表 / 我的活动
  - 报名 / 取消报名
  - 签到 / 签退
  - 签到申诉
"""
from . import client
from .context import ctx


def get_club_projects(student_id: int = None, school_id: int = None) -> dict:
    """获取俱乐部项目列表（可报名项目）"""
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
    """按类型筛选俱乐部项目"""
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
    """获取俱乐部活动列表

    参数:
      query_time: 日期 "yyyy-MM-dd"，不传则查当天
      activity_item_id: 项目 ID（从 get_club_projects 获取），筛选特定项目
    """
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
    """报名参加活动"""
    sid = student_id or ctx.user.studentId
    return client.get("v1/clubactivity/joinClubActivity", {
        "studentId": sid, "activityId": activity_id
    })


def cancel_activity(student_id: int = None, activity_id: int = 0) -> dict:
    """取消报名"""
    sid = student_id or ctx.user.studentId
    return client.get("v1/clubactivity/cancelActivity", {
        "studentId": sid, "activityId": activity_id
    })


def get_my_activities(student_id: int = None, page: int = 1, size: int = 15) -> dict:
    """获取我已报名的活动列表"""
    sid = student_id or ctx.user.studentId
    return client.get("v1/clubactivity/queryMyActivityList", {
        "studentId": sid, "pageNo": page, "pageSize": size
    })


def get_club_records(student_id: int = None, page: int = 1, size: int = 10) -> dict:
    """获取俱乐部打卡记录"""
    sid = student_id or ctx.user.studentId
    return client.get("v1/clubactivity/getStudentClubRecord", {
        "studentId": sid, "pageNo": page, "pageSize": size
    })


def get_club_banner(school_id: int = None) -> dict:
    """获取俱乐部横幅（鸡汤）"""
    sid = school_id or ctx.user.schoolId
    return client.get("v1/banner/querySchoolBannerChickenSoup", {"schoolId": sid})


def join_or_cancel_semester(config_id: int, type_: str) -> dict:
    """加入或取消学期俱乐部活动（type=add/remove）"""
    return client.get("v1/clubactivity/joinOrCancelSchoolSemesterActivity", {
        "configurationId": config_id, "type": type_
    })


def get_semester_activities(week_day: str = None, activity_item_id: int = None,
                            page: int = 1, size: int = 15) -> dict:
    """查询学期俱乐部活动"""
    params = {"pageNo": page, "pageSize": size}
    if week_day:
        params["weekDay"] = week_day
    if activity_item_id is not None:
        params["activityItemId"] = activity_item_id
    return client.get("v1/clubactivity/querySemesterClubActivity", params)


def get_my_semester_activities() -> dict:
    """查询我的学期俱乐部活动"""
    return client.get("v1/clubactivity/queryMySemesterClubActivity")


def get_sign_in_tf(student_id: int = None) -> dict:
    """获取当前签到状态（是否可签到/签退）

    返回 SignInTf：
      signStatus: "0"=未签到，"1"=已签到
      signInStatus / signBackStatus
      activityId / activityName / address / lat/lng / time
    """
    sid = student_id or ctx.user.studentId
    return client.get("v1/clubactivity/getSignInTf", {"studentId": sid})


def sign_in_or_back(activity_id: int, latitude: str, longitude: str,
                    sign_type: str = "1", student_id: int = None) -> dict:
    """签到或签退

    对应 Java SignBody：
      sign_type: "1"=签到, "2"=签退
      latitude/longitude: 签到时的 GPS 坐标
    """
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
    """签退申诉

    对应 Java SignAppealBody：
      apply_type: 申诉类型
      reason: 申诉原因
      pic1-3: 图片凭证
    """
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
    """获取申诉说明"""
    return client.get("v1/clubactivity/getApplyIntroduce")


def count_valid_sign_up(student_id: int = None) -> dict:
    """统计有效报名数"""
    params = {}
    if student_id is not None:
        params["studentId"] = student_id
    elif ctx.user.studentId:
        params["studentId"] = ctx.user.studentId
    return client.get("v1/clubactivity/countValidSignUp", params)


def add_advice(body: dict) -> dict:
    """提交建议"""
    return client.post("v1/clubactivity/addAdvice", body)


def get_advice_types() -> dict:
    """获取建议类型列表"""
    return client.get("v1/clubactivity/getAdviceTypeList")


def get_home_club() -> dict:
    """首页俱乐部活动 Top 3"""
    return client.get("v1/clubactivity/querySchoolActivityTopThree")
