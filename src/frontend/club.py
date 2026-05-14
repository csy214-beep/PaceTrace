from datetime import datetime, timedelta

import streamlit as st

from api import club
from frontend.utils import api_call, get_activity_window
from lib.geo import random_point
from scheduler import load_club_state, save_club_state
from tray.tray import notify
from frontend.logger import logger

def get_sign_status(a, sd, cur_aid):
    return a["clubActivityId"] == cur_aid and sd.get("signStatus") == "1"


def show_club_page():
    st.markdown("#### 学期项目")
    sem_data = st.session_state.semester_acts
    sem_list = sem_data.get("response") if sem_data else []
    if sem_list:
        for s in sem_list:
            joined = s.get("joinStatus") == "1"
            status = "已加入" if joined else "未加入"
            st.markdown(
                f"<div class='card'><div><b>{s.get('activityName')}</b> "
                f"<span class='{'tag-ok' if joined else ''}' style='font-size:0.85rem;{'color:#2e7d32' if joined else 'color:#888'}'>"
                f"{status}</span></div>"
                f"<div class='card-sm'>{s.get('addressDetail')} | {s.get('weekDay')} "
                f"{s.get('startTime')}-{s.get('endTime')} | 人数 {s.get('joinStudentNum')}/{s.get('studentNum')}</div></div>",
                unsafe_allow_html=True,
            )
            if not joined:
                if st.button(
                    f"加入 {s.get('activityName')}",
                    key=f"js_{s['configurationId']}",
                    use_container_width=True,
                ):
                    r = api_call(club.join_or_cancel_semester, s["configurationId"], "add")
                    if r:
                        if r.get("code") == 10000:
                            st.success("加入成功")
                            notify("行迹", f"已加入: {s.get('activityName')}")
                            st.session_state.club_types = api_call(club.get_club_projects)
                            st.session_state.semester_acts = api_call(club.get_semester_activities)
                            st.rerun()
                        else:
                            st.error(f"加入失败: {r.get('msg', '未知错误')}")
                            notify("行迹", f"加入失败: {r.get('msg', '未知错误')}")
            else:
                if st.button(
                    f"退出 {s.get('activityName')}",
                    key=f"qs_{s['configurationId']}",
                    use_container_width=True,
                ):
                    r = api_call(club.join_or_cancel_semester, s["configurationId"], "remove")
                    if r:
                        if r.get("code") == 10000:
                            st.success("已退出")
                            notify("行迹", f"已退出: {s.get('activityName')}")
                            st.session_state.club_types = api_call(club.get_club_projects)
                            st.session_state.semester_acts = api_call(club.get_semester_activities)
                            st.rerun()
                        else:
                            st.error(f"退出失败: {r.get('msg', '未知错误')}")
    else:
        st.caption("暂无学期项目")

    st.divider()
    st.markdown("#### 报名活动")
    types_data = st.session_state.club_types
    types_list = types_data.get("response") if types_data else []
    if not types_list:
        st.warning("尚未加入任何学期项目，请先加入")
    else:
        WEEKDAY_CN = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        date_opts = []
        date_map = {}
        for i in range(14):
            d = datetime.now() + timedelta(days=i)
            if d.weekday() >= 5:
                continue
            label = f"{d.strftime('%Y-%m-%d')} {WEEKDAY_CN[d.weekday()]}"
            date_opts.append(label)
            date_map[label] = d.strftime("%Y-%m-%d")
        sel_label = st.selectbox("日期", date_opts, index=0, key="act_date_sel")
        sel_date = date_map[sel_label]
        type_opts = {f"{t.get('itemName')}": t.get("itemId") for t in types_list}
        sel_type_label = st.selectbox("项目类型", list(type_opts.keys()), key="act_type_sel")
        sel_type_id = type_opts[sel_type_label]

        if st.button("查询活动", use_container_width=True, type="primary"):
            with st.spinner("查询中..."):
                st.session_state.activities = api_call(
                    club.get_activity_list,
                    query_time=sel_date,
                    activity_item_id=sel_type_id,
                    page=1,
                    size=50,
                )
            st.session_state.activity_query_done = True
            st.rerun()

        acts = st.session_state.activities
        alist = acts.get("response") if acts else []
        if alist:
            my_ids = {a["clubActivityId"] for a in (st.session_state.my_acts.get("response") or [])}
            for a in alist:
                full = a.get("signInStudent", 0) >= a.get("maxStudent", 1)
                already = a["clubActivityId"] in my_ids
                if full:
                    tag = '<span class="tag-full">已满</span>'
                elif already:
                    tag = '<span class="tag-ok">已报名</span>'
                else:
                    tag = '<span class="tag-ok">可报</span>'
                intro = a.get("clubIntroduction", "") or ""
                st.markdown(
                    f"<div class='card'><div><b>{a.get('activityName')}</b> {tag}</div>"
                    f"<div class='card-sm'>{a.get('addressDetail')} | {a.get('teacherName', '')} | "
                    f"{a.get('startTime')}-{a.get('endTime')}</div>"
                    f"<div class='card-sm'>已报 {a.get('signInStudent')}/{a.get('maxStudent')} 人"
                    f"{' | ' + intro if intro else ''}</div></div>",
                    unsafe_allow_html=True,
                )
                if not full and not already:
                    if st.button(
                        "报名",
                        key=f"join_{a['clubActivityId']}",
                        use_container_width=True,
                        type="primary",
                    ):
                        r = api_call(club.join_activity, activity_id=a["clubActivityId"])
                        if r:
                            resp_data = r.get("response") or {}
                            ok = r.get("code") == 10000
                            if isinstance(resp_data, dict):
                                ok = ok and resp_data.get("status") != "0"
                            if ok:
                                st.success("报名成功")
                                notify("行迹", f"报名成功: {a.get('activityName')}")
                                st.session_state.my_acts = api_call(club.get_my_activities)
                                st.rerun()
                            else:
                                msg = resp_data.get("message", "") if isinstance(resp_data, dict) else str(resp_data)
                                msg = msg or r.get("msg", "未知错误")
                                st.error(f"报名失败: {msg}")
                                notify("行迹", f"报名失败: {msg}")
                if already:
                    if st.button(
                        "取消报名",
                        key=f"cancel_{a['clubActivityId']}",
                        use_container_width=True,
                    ):
                        r = api_call(club.cancel_activity, activity_id=a["clubActivityId"])
                        if r:
                            resp_data = r.get("response") or {}
                            ok = r.get("code") == 10000
                            if isinstance(resp_data, dict):
                                ok = ok and resp_data.get("status") != "0"
                            if ok:
                                st.success("已取消")
                                notify("行迹", f"已取消报名: {a.get('activityName')}")
                                st.session_state.my_acts = api_call(club.get_my_activities)
                                st.rerun()
                            else:
                                msg = resp_data.get("message", "") if isinstance(resp_data, dict) else str(resp_data)
                                msg = msg or r.get("msg", "未知错误")
                                st.error(f"取消失败: {msg}")
                                notify("行迹", f"取消失败: {msg}")
        else:
            if st.session_state.get("activity_query_done"):
                rd_check = (st.session_state.run_info or {}).get("response") or {}
                if rd_check.get("runValidDay", 0) >= 40:
                    st.info("可能学期要求已达标，请自行确认")
                else:
                    st.info("该日期暂无活动，请换一天试试")

    st.divider()
    st.markdown("#### 我的活动")

    st.session_state.my_acts = api_call(club.get_my_activities)
    mya = st.session_state.my_acts
    mylist = mya.get("response") if mya else []
    if mylist:
        sign_tf = api_call(club.get_sign_in_tf)
        sd = sign_tf.get("response") if sign_tf else {}
        cur_aid = sd.get("activityId")
        now = datetime.now()

        upcoming = []
        history = []
        for a in mylist:
            mmdd = a.get("mmdd", "")
            start_str = a.get("startTime", "")
            end_str = a.get("endTime", "")
            _, end_dt = get_activity_window(mmdd, start_str, end_str)
            if end_dt and end_dt < now:
                history.append(a)
            else:
                upcoming.append(a)

        if not upcoming and not history:
            st.caption("暂无报名记录")
        else:
            if upcoming:
                st.markdown("##### 待签到 / 待签退")

                auto_key = "auto_sign_enabled"
                if auto_key not in st.session_state:
                    st.session_state[auto_key] = load_club_state().get("enabled", False)

                c_auto1, c_auto2 = st.columns([2, 1])
                with c_auto1:
                    if st.button(
                        "自动签到/签退 (开启)" if not st.session_state[auto_key]
                        else "自动签到/签退 (关闭)",
                        key="auto_sign_toggle",
                        use_container_width=True,
                    ):
                        st.session_state[auto_key] = not st.session_state[auto_key]
                        cfg = load_club_state()
                        cfg["enabled"] = st.session_state[auto_key]
                        save_club_state(cfg)
                        st.rerun()
                with c_auto2:
                    if load_club_state().get("enabled", False):
                        st.success("运行中")
                    else:
                        st.caption("每60秒检测一次")

                if st.session_state[auto_key]:
                    st.warning("此功能需保持程序常驻后台运行，请勿在其它设备登录当前账号")

                for a in upcoming:
                    is_signed = get_sign_status(a, sd, cur_aid)
                    is_cur = a["clubActivityId"] == cur_aid
                    tag = (
                        '<span class="tag-sb">待签退</span>'
                        if is_signed
                        else '<span class="tag-si">待签到</span>'
                    )
                    label = "签退" if is_signed else "签到"
                    k = (
                        f"sback_{a['clubActivityId']}"
                        if is_signed
                        else f"sin_{a['clubActivityId']}"
                    )
                    ti = f"{a.get('mmdd')} {a.get('startTime')}-{a.get('endTime')}"
                    st.markdown(
                        f"<div class='card'><div><b>{a.get('activityName')}</b> {tag}</div>"
                        f"<div class='card-sm'>{ti} | {a.get('addressDetail')}</div></div>",
                        unsafe_allow_html=True,
                    )

                    mmdd = a.get("mmdd", "")
                    start_str = a.get("startTime", "")
                    end_str = a.get("endTime", "")
                    start_dt, end_dt = get_activity_window(mmdd, start_str, end_str)

                    c1, c2 = st.columns([3, 1])
                    if sd.get("latitude") and sd.get("longitude"):
                        lat_v, lng_v = random_point(
                            sd["latitude"], sd["longitude"], 100
                        )
                        st.caption(
                            f"({sd['latitude']}, {sd['longitude']}) +{100}m 随机偏移"
                        )
                    else:
                        lat_v, lng_v = None, None
                    with c1:
                        if not lat_v or not lng_v:
                            window_info = ""
                            if start_dt and end_dt:
                                window_info = f"（活动窗口 {start_dt.strftime('%H:%M')}-{end_dt.strftime('%H:%M')}，需等待老师开放签到）"
                            st.caption(f"签到暂不可用{window_info}")
                        elif st.button(
                            label, key=k, use_container_width=True, type="primary"
                        ):
                            r = api_call(
                                club.sign_in_or_back,
                                a["clubActivityId"],
                                lat_v,
                                lng_v,
                                "1" if label == "签到" else "2",
                            )
                            if r:
                                resp_data = r.get("response") or {}
                                msg = (
                                    resp_data.get("message", "")
                                    if isinstance(resp_data, dict)
                                    else str(resp_data)
                                )
                                msg = msg or r.get("msg", "未知错误")
                                if r.get("code") == 10000:
                                    st.success(f"{label}成功")
                                    notify("行迹", f"{label}成功")
                                    logger.info(
                                        "%s成功: activity=%s",
                                        label,
                                        a["clubActivityId"],
                                    )
                                else:
                                    st.error(f"{label}失败: {msg}")
                                    notify("行迹", f"{label}失败: {msg}")
                                    logger.warning(
                                        "%s失败: activity=%s msg=%s",
                                        label,
                                        a["clubActivityId"],
                                        msg,
                                    )
                                if r.get("code") == 10000:
                                    st.rerun()
                    with c2:
                        if st.button(
                            "取消报名",
                            key=f"unreg_{a['clubActivityId']}",
                            use_container_width=True,
                        ):
                            r = api_call(club.cancel_activity, activity_id=a["clubActivityId"])
                            if r:
                                resp_data = r.get("response") or {}
                                ok = r.get("code") == 10000
                                if isinstance(resp_data, dict):
                                    ok = ok and resp_data.get("status") != "0"
                                if ok:
                                    st.success("已取消")
                                    notify("行迹", "报名已取消")
                                    st.rerun()
                                else:
                                    msg = resp_data.get("message", "") if isinstance(resp_data, dict) else str(resp_data)
                                    msg = msg or r.get("msg", "未知错误")
                                    st.error(f"取消失败: {msg}")
            if history:
                with st.expander(f"历史记录 ({len(history)} 条)"):
                    for a in history:
                        ti = f"{a.get('mmdd')} {a.get('startTime')}-{a.get('endTime')}"
                        st.markdown(
                            f"<div class='card'><div><b>{a.get('activityName')}</b></div>"
                            f"<div class='card-sm'>{ti} | {a.get('addressDetail')}</div></div>",
                            unsafe_allow_html=True,
                        )
    else:
        st.caption("暂无报名记录")
