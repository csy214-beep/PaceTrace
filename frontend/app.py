import json
import os
import sys
import math
import random
import tempfile
from datetime import datetime, timedelta

import streamlit as st
import pandas as pd
import folium

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

def _load_env():
    path = os.path.join(os.path.dirname(__file__), "..", ".env")
    if os.path.exists(path):
        for line in open(path, encoding="utf-8"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip()

_load_env()

from api import auth, run, club, ctx
from frontend.logger import logger

st.set_page_config(page_title="行迹", page_icon=None, layout="centered")

st.markdown("""
<style>
    #MainMenu, header, footer { visibility: hidden; }
    .block-container { padding-top: 0.5rem; max-width: 720px; }
    section[data-testid="stSidebar"] { width: 180px !important; min-width: 180px !important; }
    section[data-testid="stSidebar"] .block-container { padding: 0.8rem; }
    section[data-testid="stSidebar"] hr { margin: 0.4rem 0; }
    .card { background:#fafafa; border-radius:10px; padding:0.8rem; margin-bottom:0.5rem; border:1px solid #eee; }
    .card-sm { font-size:0.85rem; color:#666; }
    .tag-ok { background:#e8f5e9; color:#2e7d32; border-radius:10px; padding:1px 8px; font-size:0.75rem; }
    .tag-full { background:#fbe9e7; color:#c62828; border-radius:10px; padding:1px 8px; font-size:0.75rem; }
    .tag-si { background:#e3f2fd; color:#1565c0; border-radius:10px; padding:1px 8px; font-size:0.75rem; }
    .tag-sb { background:#fff3e0; color:#e65100; border-radius:10px; padding:1px 8px; font-size:0.75rem; }
    div[data-testid="stMetricValue"] { font-size:1.4rem !important; }
    .center-box { max-width:360px; margin:4rem auto; text-align:center; }
</style>
""", unsafe_allow_html=True)


def api_call(func, *args, **kwargs):
    name = func.__name__
    try:
        r = func(*args, **kwargs)
        code = r.get("code") if r else -1
        logger.info("api_call %s code=%s", name, code)
        if code == 30005:
            logger.warning("login expired, redirecting")
            st.session_state.clear()
            auth.logout()
            st.rerun()
        return r
    except Exception as e:
        logger.error("api_call %s failed: %s", name, e)
        st.error(f"请求失败: {e}")
        return None


MAPS_DIR = os.path.join(os.path.dirname(__file__), "..", "maps")
AMAP_KEY = os.environ.get("AMAP_KEY", "")

def load_maps():
    items = []
    if not os.path.isdir(MAPS_DIR):
        return items
    for f in sorted(os.listdir(MAPS_DIR)):
        if not f.endswith(".json"):
            continue
        try:
            with open(os.path.join(MAPS_DIR, f), encoding="utf-8") as fh:
                data = json.load(fh)
            raw = data.get("mapData", [])
            pts = []
            for p in raw:
                lng, lat = p.split(",")
                pts.append([float(lat), float(lng)])
            if pts:
                items.append({"id": data.get("mapId", f), "name": data.get("mapName", f), "coords": pts})
        except Exception:
            pass
    return items

all_maps = load_maps()

def route_distance(coords):
    d = 0
    for i in range(1, len(coords)):
        a, b = coords[i-1], coords[i]
        dx = (b[1] - a[1]) * 111320 * math.cos(math.radians((a[0] + b[0]) / 2))
        dy = (b[0] - a[0]) * 111320
        d += math.sqrt(dx*dx + dy*dy)
    return int(d)

def build_track(coords, target_dist):
    full_d = route_distance(coords)
    if full_d <= 0:
        return coords
    n = len(coords)
    start = random.randint(0, n - 1)
    result = []
    i = start
    while route_distance(result) < target_dist:
        result.append(coords[i])
        i = (i + 1) % n
    return result

def draw_map_folium(coords):
    lat0 = sum(c[0] for c in coords) / len(coords)
    lng0 = sum(c[1] for c in coords) / len(coords)
    if AMAP_KEY:
        tiles = f"https://webrd01.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={{x}}&y={{y}}&z={{z}}&key={AMAP_KEY}"
        attr = 'AMap'
    else:
        tiles = "OpenStreetMap"
        attr = "OSM"
    m = folium.Map(location=[lat0, lng0], zoom_start=16, tiles=tiles, attr=attr, control_scale=True, zoom_control=False)
    folium.PolyLine(coords, color="#FF4B4B", weight=3, opacity=0.85).add_to(m)
    folium.CircleMarker(coords[0], radius=5, color="#FF4B4B", fill=True).add_to(m)
    folium.CircleMarker(coords[-1], radius=5, color="#FF4B4B", fill=True).add_to(m)
    # Save to temp file and use iframe
    tmp = tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w", encoding="utf-8")
    tmp.write(m.get_root().render())
    tmp.close()
    return tmp.name


if "page" not in st.session_state:
    st.session_state.page = "首页"
for k in ["run_info", "records", "activities", "my_acts", "club_types", "semester_acts", "log_content"]:
    if k not in st.session_state:
        st.session_state[k] = None

PAGES = ["首页", "跑步", "俱乐部", "我的"]


if not ctx.user.studentId:
    st.markdown("<div class='center-box'>", unsafe_allow_html=True)
    st.markdown("### 行迹")
    st.markdown("Campus Run Management")
    st.divider()
    with st.form("login_f"):
        st.text_input("手机号", key="login_phone")
        st.text_input("密码", type="password", key="login_pwd")
        if st.form_submit_button("登录", use_container_width=True, type="primary"):
            r = api_call(auth.login, st.session_state.login_phone, st.session_state.login_pwd)
            if r and r.get("code") == 10000:
                st.rerun()
            elif r:
                st.error("账号或密码错误")
    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()


with st.sidebar:
    st.markdown(f"**{ctx.user.studentName}**")
    st.caption(ctx.user.schoolName)
    st.divider()
    for p in PAGES:
        if st.button(p, key=f"nav_{p}", use_container_width=True):
            st.session_state.page = p
            st.rerun()
    st.divider()
    if st.button("退出", use_container_width=True, key="sb_logout"):
        auth.logout()
        st.rerun()


def ensure_cache():
    if st.session_state.run_info is None:
        st.session_state.run_info = api_call(run.get_run_info)
    if st.session_state.records is None:
        st.session_state.records = api_call(run.get_run_records, 1, 10)
    if st.session_state.my_acts is None:
        st.session_state.my_acts = api_call(club.get_my_activities)
    if st.session_state.club_types is None:
        st.session_state.club_types = api_call(club.get_club_projects)
    if st.session_state.semester_acts is None:
        st.session_state.semester_acts = api_call(club.get_semester_activities)

ensure_cache()
page = st.session_state.page


# ═══════════════ 首页 ═══════════════
if page == "首页":
    ri = st.session_state.run_info
    rd = ri.get("response") if ri else {}
    if rd:
        c1, c2, c3 = st.columns(3)
        c1.metric("跑步天数", rd.get("runValidDay", 0))
        c2.metric("总距离(米)", rd.get("runValidDistance", 0))
        c3.metric("配速", rd.get("showSpeed", "-"))
    st.divider()
    st.markdown("#### 最近跑步")
    recs = st.session_state.records
    rl = recs.get("response") if recs else []
    if rl:
        for r in rl[:5]:
            st.markdown(f"<div class='card'><div><b>{r.get('recordDate')}</b> {r.get('defeatedInfo')}</div><div class='card-sm'>{r.get('runValidDistance')}m | {r.get('runValidTime')}min | {r.get('runSpeed')}m/min</div></div>", unsafe_allow_html=True)
    st.divider()
    st.markdown("#### 俱乐部热门")
    hc = api_call(club.get_home_club)
    hl = hc.get("response") if hc else []
    if hl:
        for a in hl:
            full = int(a.get("applyStudentCount", 0)) >= int(a.get("maxStudent", 1))
            tag = '<span class="tag-full">已满</span>' if full else '<span class="tag-ok">可报</span>'
            st.markdown(f"<div class='card'><div>{a.get('activityName')} {tag}</div><div class='card-sm'>{a.get('startTime')} | {a.get('addressDetail')} | {a.get('applyStudentCount')}/{a.get('maxStudent')}</div></div>", unsafe_allow_html=True)


# ═══════════════ 跑步 ═══════════════
elif page == "跑步":
    if not all_maps:
        st.info("maps 目录下没有路线文件")
    else:
        names = [m["name"] for m in all_maps]
        sel_name = st.selectbox("选择路线", names, key="map_sel")
        sel_map = next(m for m in all_maps if m["name"] == sel_name)
        full_dist = route_distance(sel_map["coords"])
        st.caption(f"路线全长约 {full_dist} 米")

        if "init_dist" not in st.session_state:
            st.session_state.init_dist = random.randint(1000, 6000)
        init_dist = st.session_state.init_dist
        init_pace = random.uniform(4.0, 7.0)
        init_time = max(1, int(init_dist / (init_pace * 1000 / 3600) / 60))

        c1, c2 = st.columns(2)
        with c1:
            dist = st.number_input("跑步距离(米)", 0, 10000, init_dist, key="run_dist")
        with c2:
            duration = st.number_input("时长(分钟)", 0, 180, init_time, key="run_dur")

        speed_ok = True
        if duration > 0:
            speed_kmh = (dist / (duration * 60)) * 3.6
            if speed_kmh > 12:
                st.warning(f"速度 {speed_kmh:.1f} km/h 超过上限")
                speed_ok = False
            elif speed_kmh > 0:
                st.caption(f"配速约 {speed_kmh:.1f} km/h")

        track = build_track(sel_map["coords"], dist)
        if not AMAP_KEY:
            st.info(
                "当前使用 OpenStreetMap 预览，效果一般。如需高德地图精确定位，请在项目根目录 .env 文件中设置高德JS API Key"
            )
        map_path = draw_map_folium(track)
        st.iframe(map_path, height=400)

        pts_str = json.dumps([f"{p[1]},{p[0]}" for p in track], ensure_ascii=False)
        if speed_ok and st.button("提交跑步记录", key="run_submit", type="primary", use_container_width=True):
            r = api_call(run.save_run_record_v2,
                distance=dist, time=duration,
                track_points=pts_str, vocal_status="1",
                record_date=datetime.now().strftime("%Y-%m-%d"))
            if r:
                code = r.get("code")
                if code == 10000:
                    st.success("提交成功")
                    st.session_state.run_info = api_call(run.get_run_info)
                    st.session_state.records = api_call(run.get_run_records, 1, 10)
                    st.session_state.init_dist = random.randint(1000, 6000)
                else:
                    st.error(f"提交失败: {r.get('msg', '未知错误')}")

    st.divider()
    st.markdown("#### 跑步记录")
    if st.button("刷新", use_container_width=True, key="ref_rec"):
        st.session_state.records = api_call(run.get_run_records, 1, 10)
        st.rerun()
    recs2 = st.session_state.records
    rl2 = recs2.get("response") if recs2 else []
    if rl2:
        for r in rl2:
            st.markdown(f"<div class='card'><div><b>{r.get('recordDate')}</b> {r.get('defeatedInfo')}</div><div class='card-sm'>{r.get('runValidDistance')}m | {r.get('runValidTime')}min | {r.get('runSpeed')}m/min</div></div>", unsafe_allow_html=True)


# ═══════════════ 俱乐部 ═══════════════
elif page == "俱乐部":
    st.markdown("#### 学期项目")
    sem_data = st.session_state.semester_acts
    sem_list = sem_data.get("response") if sem_data else []
    if sem_list:
        for s in sem_list:
            joined = s.get("joinStatus") == "1"
            status = "已加入" if joined else "未加入"
            st.markdown(f"<div class='card'><div><b>{s.get('activityName')}</b> <span style='color:{'#2e7d32' if joined else '#888'}'>{status}</span></div><div class='card-sm'>{s.get('addressDetail')} | {s.get('weekDay')} {s.get('startTime')}-{s.get('endTime')} | 人数 {s.get('joinStudentNum')}/{s.get('studentNum')}</div></div>", unsafe_allow_html=True)
            if not joined:
                if st.button(f"加入 {s.get('activityName')}", key=f"js_{s['configurationId']}", use_container_width=True):
                    r = api_call(club.join_or_cancel_semester, s["configurationId"], "add")
                    if r and r.get("code") == 10000:
                        st.success("加入成功")
                        st.session_state.club_types = api_call(club.get_club_projects)
                        st.session_state.semester_acts = api_call(club.get_semester_activities)
                        st.rerun()
            else:
                if st.button(f"退出 {s.get('activityName')}", key=f"qs_{s['configurationId']}", use_container_width=True):
                    r = api_call(club.join_or_cancel_semester, s["configurationId"], "remove")
                    if r and r.get("code") == 10000:
                        st.success("已退出")
                        st.session_state.club_types = api_call(club.get_club_projects)
                        st.session_state.semester_acts = api_call(club.get_semester_activities)
                        st.rerun()
    else:
        st.caption("暂无学期项目")

    st.divider()
    st.markdown("#### 报名活动")
    types_data = st.session_state.club_types
    types_list = types_data.get("response") if types_data else []
    if not types_list:
        st.warning("尚未加入任何学期项目，请先加入")
    else:
        date_opts = [(datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(14)]
        sel_date = st.selectbox("日期", date_opts, index=0, key="act_date_sel")
        type_opts = {f"{t.get('itemName')}": t.get("itemId") for t in types_list}
        sel_type_label = st.selectbox("项目类型", list(type_opts.keys()), key="act_type_sel")
        sel_type_id = type_opts[sel_type_label]

        if st.button("查询活动", use_container_width=True, type="primary"):
            with st.spinner("查询中..."):
                st.session_state.activities = api_call(club.get_activity_list, query_time=sel_date, activity_item_id=sel_type_id, page=1, size=50)
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
                st.markdown(f"<div class='card'><div><b>{a.get('activityName')}</b> {tag}</div><div class='card-sm'>{a.get('addressDetail')} | {a.get('teacherName', '')} | {a.get('startTime')}-{a.get('endTime')}</div><div class='card-sm'>已报 {a.get('signInStudent')}/{a.get('maxStudent')} 人{' | ' + intro if intro else ''}</div></div>", unsafe_allow_html=True)
                if not full and not already:
                    if st.button("报名", key=f"join_{a['clubActivityId']}", use_container_width=True, type="primary"):
                        r = api_call(club.join_activity, activity_id=a["clubActivityId"])
                        if r and r.get("code") == 10000:
                            st.success("报名成功")
                            st.session_state.my_acts = api_call(club.get_my_activities)
                            st.rerun()
                if already:
                    if st.button("取消报名", key=f"cancel_{a['clubActivityId']}", use_container_width=True):
                        r = api_call(club.cancel_activity, activity_id=a["clubActivityId"])
                        if r and r.get("code") == 10000:
                            st.success("已取消")
                            st.session_state.my_acts = api_call(club.get_my_activities)
                            st.rerun()
        else:
            if st.session_state.get("activity_query_done"):
                rd_check = (st.session_state.run_info or {}).get("response") or {}
                if rd_check.get("runValidDay", 0) >= 40:
                    st.info("可能学期要求已达标，请自行确认")
                else:
                    st.info("该日期暂无活动，请换一天试试")

    st.divider()
    st.markdown("#### 需处理的活动")

    def get_sign_status(a, sd, cur_aid):
        if a["clubActivityId"] == cur_aid:
            return sd.get("signStatus") == "1"
        return a.get("signStatus") == "1"

    st.session_state.my_acts = api_call(club.get_my_activities)
    mya = st.session_state.my_acts
    mylist = mya.get("response") if mya else []
    if mylist:
        sign_tf = api_call(club.get_sign_in_tf)
        sd = sign_tf.get("response") if sign_tf else {}
        cur_aid = sd.get("activityId")
        today_mmdd = datetime.now().strftime("%m-%d")

        upcoming = []
        history = []
        for a in mylist:
            is_signed = get_sign_status(a, sd, cur_aid)
            act_date = a.get("mmdd", "")
            if act_date < today_mmdd:
                history.append(a)
            else:
                upcoming.append(a)

        if not upcoming and not history:
            st.caption("暂无报名记录")
        else:
            if upcoming:
                st.markdown("##### 待签到 / 待签退")
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
                        f"<div class='card'><div><b>{a.get('activityName')}</b> {tag}</div><div class='card-sm'>{ti} | {a.get('addressDetail')}</div></div>",
                        unsafe_allow_html=True,
                    )
                    c1, c2 = st.columns([3, 1])
                    has_ll = bool(sd.get("latitude") and sd.get("longitude"))
                    lat_v = sd["latitude"] if (is_cur and has_ll) else "30.552"
                    lng_v = sd["longitude"] if (is_cur and has_ll) else "103.994"
                    with c1:
                        if st.button(
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
                                st.success(
                                    f"{label}成功"
                                    if r.get("code") == 10000
                                    else f"{label}失败: {r.get('msg', '未知错误')}"
                                )
                                if r.get("code") == 10000:
                                    st.rerun()
                    with c2:
                        if st.button(
                            "取消报名",
                            key=f"unreg_{a['clubActivityId']}",
                            use_container_width=True,
                        ):
                            r = api_call(
                                club.cancel_activity, activity_id=a["clubActivityId"]
                            )
                            if r and r.get("code") == 10000:
                                st.success("已取消")
                                st.rerun()
            if history:
                with st.expander(f"历史记录 ({len(history)} 条)"):
                    for a in history:
                        ti = f"{a.get('mmdd')} {a.get('startTime')}-{a.get('endTime')}"
                        st.markdown(
                            f"<div class='card'><div><b>{a.get('activityName')}</b></div><div class='card-sm'>{ti} | {a.get('addressDetail')}</div></div>",
                            unsafe_allow_html=True,
                        )
    else:
        st.caption("暂无报名记录")


# ═══════════════ 我的 ═══════════════
elif page == "我的":
    st.markdown(f"**{ctx.user.studentName}**")
    st.caption(f"{ctx.user.schoolName} | {ctx.user.className} | 学号 {ctx.user.registerCode}")
    st.divider()
    st.markdown("#### 运动统计")
    if st.button("刷新", use_container_width=True, key="ref_stats"):
        st.session_state.run_info = api_call(run.get_run_info)
        st.rerun()
    ri3 = st.session_state.run_info
    rd3 = ri3.get("response") if ri3 else {}
    if rd3:
        c1, c2, c3 = st.columns(3)
        c1.metric("有效天数", rd3.get("runValidDay", 0))
        c2.metric("总距离(米)", rd3.get("runValidDistance", 0))
        c3.metric("配速", rd3.get("showSpeed", "-"))
    st.divider()
    st.markdown("#### 操作日志")
    if st.button("刷新日志", use_container_width=True, key="ref_log"):
        log_path = os.path.join(os.path.dirname(__file__), "logs", "app.log")
        if os.path.exists(log_path):
            with open(log_path, encoding="utf-8") as f:
                st.session_state.log_content = f.read()
    with st.expander("查看详细日志"):
        st.text_area("日志内容", st.session_state.log_content or "", height=400, label_visibility="collapsed")
