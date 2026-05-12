"""
行迹 PaceTrace API 交互式测试

所有文件仅保存于当前项目目录 (api/.token, api/.user)。
登录后用户信息自动填充到内存 ctx.user，后续请求自动取用。
"""

import json
from api import auth, run, club, ctx


def pp(resp: dict):
    code = resp.get("code")
    msg = resp.get("msg", "")
    print(f"code: {code}  msg: {msg}")
    data = resp.get("response")
    if data is not None:
        s = json.dumps(data, indent=2, ensure_ascii=False)
        if len(s) > 2000:
            print(s[:2000] + "\n... (truncated)")
        else:
            print(s)
    print("-" * 65)


def cmd_login():
    phone = input("手机号: ").strip()
    pwd = input("密码: ").strip()
    if not phone or not pwd:
        return
    r = auth.login(phone, pwd)
    pp(r)
    if r.get("code") == 10000 and ctx.user.studentName:
        print(f"欢迎 {ctx.user.studentName}  ({ctx.user.schoolName})")
    elif r.get("code") == 40000:
        print("账号或密码错误")


def cmd_logout():
    auth.logout()
    print("已退出，用户信息已清除")


def cmd_whoami():
    if ctx.user.studentId:
        print(f"用户: {ctx.user.studentName}  [{ctx.user.schoolName}]")
        print(f"学号: {ctx.user.registerCode}  班级: {ctx.user.className}")
    else:
        print("未登录")


def cmd_run_info():
    pp(run.get_run_info())


def cmd_run_standard():
    pp(run.get_run_standard())


def cmd_run_records():
    pp(run.get_run_records())


def cmd_schools():
    pp(auth.get_schools())


def cmd_rank():
    pp(run.get_rank())
    print("首页排名:")
    pp(run.get_home_rank())


def cmd_club_projects():
    pp(club.get_club_projects())


def cmd_activities():
    date = input("日期 yyyy-MM-dd (回车=今天): ").strip()
    item_id = input("项目ID (回车=全部): ").strip()
    pp(club.get_activity_list(
        query_time=date or None,
        activity_item_id=int(item_id) if item_id else None,
    ))


def cmd_activities_next_days():
    days = int(input("查未来几天 (默认3): ").strip() or "3")
    item_id = input("项目ID (回车=全部): ").strip()
    from datetime import datetime, timedelta
    for i in range(days):
        d = (datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d")
        print(f"\n--- {d} ---")
        r = club.get_activity_list(
            query_time=d,
            activity_item_id=int(item_id) if item_id else None,
        )
        data = r.get("response") or []
        if data:
            for a in data:
                print(f"  [{a.get('clubActivityId')}] {a.get('activityName')}  "
                      f"{a.get('startTime')}-{a.get('endTime')}  "
                      f"{a.get('signInStudent')}/{a.get('maxStudent')}")
        else:
            print("  (无)" if r.get("code") == 10000 else f"  error code={r.get('code')}")


def cmd_home_club():
    pp(club.get_home_club())


def cmd_club_banner():
    sid = input("school_id (回车用当前): ").strip()
    pp(club.get_club_banner(int(sid) if sid else None))


def cmd_sign_in_tf():
    pp(club.get_sign_in_tf())


def cmd_club_records():
    pp(club.get_club_records())


def cmd_my_activities():
    pp(club.get_my_activities())


def cmd_join_activity():
    aid = int(input("activity_id: ").strip())
    pp(club.join_activity(activity_id=aid))


def cmd_cancel_activity():
    aid = int(input("activity_id: ").strip())
    pp(club.cancel_activity(activity_id=aid))


def cmd_sign():
    """签到流程：先查状态 -> 再签到"""
    tf = club.get_sign_in_tf()
    pp(tf)
    if tf.get("code") != 10000:
        return
    data = tf.get("response") or {}
    if data.get("signStatus") == "0":
        aid = int(input("activity_id: ").strip() or (data.get("activityId") or 0))
        lat = input("纬度: ").strip() or "30.552"
        lng = input("经度: ").strip() or "103.994"
        pp(club.sign_in_or_back(aid, lat, lng, "1"))
    elif data.get("signStatus") == "1":
        print("已签到，可进行签退")
        aid = int(input("activity_id: ").strip() or (data.get("activityId") or 0))
        lat = input("纬度: ").strip() or "30.552"
        lng = input("经度: ").strip() or "103.994"
        pp(club.sign_in_or_back(aid, lat, lng, "2"))


def cmd_save_run():
    uid = ctx.user.userId or int(input("user_id: ").strip() or "0")
    dist = int(input("距离(米): ").strip() or "2000")
    t = int(input("时间(秒): ").strip() or "600")
    track = input("轨迹点JSON (留空=[]): ").strip() or "[]"
    pp(run.save_run_record_v2(
        user_id=uid, distance=dist, time=t,
        track_points=track, record_date=input("日期(2026-05-12): ").strip() or "",
    ))


def cmd_once_record():
    rid = int(input("record_id: ").strip() or "0")
    pp(run.get_once_run_record(rid))


def cmd_school_area():
    sid = input("school_id (回车用当前): ").strip()
    pp(run.get_school_area(int(sid) if sid else None))


def cmd_semester_info():
    pp(run.get_run_semester_info())


def cmd_semester_activities():
    pp(club.get_semester_activities())


def cmd_my_semester():
    pp(club.get_my_semester_activities())


def cmd_join_semester():
    cid = int(input("configuration_id: ").strip())
    pp(club.join_or_cancel_semester(cid, "add"))


def main():
    print("===== 行迹 PaceTrace API 测试 =====")
    if ctx.user.studentId:
        print(f"当前用户: {ctx.user.studentName} [{ctx.user.schoolName}]")

    menu = [
        ("1",  "登录", cmd_login),
        ("2",  "退出登录", cmd_logout),
        ("3",  "当前用户", cmd_whoami),
        ("",   "--- 校园跑 ---", None),
        ("10", "跑步信息", cmd_run_info),
        ("11", "跑步标准", cmd_run_standard),
        ("12", "跑步记录", cmd_run_records),
        ("13", "学期统计", cmd_semester_info),
        ("14", "学校区域", cmd_school_area),
        ("15", "排名", cmd_rank),
        ("16", "提交跑步记录", cmd_save_run),
        ("17", "跑步记录详情", cmd_once_record),
        ("",   "--- 俱乐部 ---", None),
        ("20", "俱乐部项目", cmd_club_projects),
        ("21", "活动列表（指定日期）", cmd_activities),
        ("21a", "活动列表（未来几天）", cmd_activities_next_days),
        ("22", "首页俱乐部", cmd_home_club),
        ("23", "俱乐部横幅", cmd_club_banner),
        ("24", "签到状态", cmd_sign_in_tf),
        ("25", "签到/签退", cmd_sign),
        ("26", "打卡记录", cmd_club_records),
        ("27", "我的活动", cmd_my_activities),
        ("28", "报名活动", cmd_join_activity),
        ("29", "取消报名", cmd_cancel_activity),
        ("30", "学期活动", cmd_semester_activities),
        ("31", "我的学期活动", cmd_my_semester),
        ("32", "加入学期活动", cmd_join_semester),
        ("",   "--- 其他 ---", None),
        ("40", "学校列表", cmd_schools),
        ("0",  "退出", lambda: exit(0)),
    ]

    while True:
        print()
        for key, label, _ in menu:
            if not key:
                print(f"  {label}")
            else:
                print(f"  {key}. {label}")
        c = input("\n选择: ").strip()
        for key, _, fn in menu:
            if key == c and fn:
                fn()
                break
        else:
            print("无效选择")


if __name__ == "__main__":
    main()
