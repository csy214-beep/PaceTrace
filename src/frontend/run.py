import json
import random
from datetime import datetime

import streamlit as st

from api import run
from api import ctx
from lib.geo import route_distance, build_track
from lib.maps import load_maps
from frontend.utils import (
    api_call,
    all_maps,
    draw_map_folium,
    AMAP_KEY,
)
from scheduler import load_run_state, save_run_state
from tray.tray import notify


def show_run_page():
    st.markdown("#### 跑步")

    # load school standard
    std_resp = api_call(run.get_run_standard)
    std = std_resp.get("response") if std_resp else {}
    gender = ("girl" if st.session_state.get("gender") == "2" else "boy") if st.session_state.get("gender") else None
    gender = gender or ("girl" if ctx.user.gender == "2" else "boy")
    once_min = std.get(f"{gender}OnceDistanceMin", 1000)
    once_max = std.get(f"{gender}OnceDistanceMax", 5000)
    total_dist = std.get(f"{gender}AllRunDistance", 80000)
    total_times = std.get(f"{gender}AllRunTime", 24)
    time_min = std.get(f"{gender}OnceTimeMin", 5)
    time_max = std.get(f"{gender}OnceTimeMax", 60)
    semester = std.get("semesterYear", "")
    first_start = std.get("firstSemesterDateStart", "")
    first_end = std.get("firstSemesterDateEnd", "")
    second_start = std.get("secondSemesterDateStart", "")
    second_end = std.get("secondSemesterDateEnd", "")

    # display standards
    with st.expander("学校标准", expanded=False):
        c1, c2, c3 = st.columns(3)
        c1.metric(f"单次距离", f"{once_min}-{once_max}米")
        c2.metric(f"单次时长", f"{time_min}-{time_max}分钟")
        c3.metric(f"学期目标", f"{total_dist/1000:.0f}公里/{total_times}次")
        if first_start:
            st.caption(f"第一学期: {first_start} ~ {first_end}")
        if second_start:
            st.caption(f"第二学期: {second_start} ~ {second_end}")

    # semester progress (current semester only)
    semester_year = std.get("semesterYear", "")
    if semester_year:
        sem_resp = api_call(run.get_run_semester_info, year_semester=semester_year)
        sem = sem_resp.get("response") if sem_resp else {}
    else:
        sem = {}
    if not sem:
        sem = {}
    cur_dist = sem.get("runValidDistance", 0) or 0
    cur_days = sem.get("runValidDay", 0) or 0
    dist_pct = min(100, int(cur_dist / total_dist * 100)) if total_dist else 0
    days_pct = min(100, int(cur_days / total_times * 100)) if total_times else 0

    with st.expander("学期进度", expanded=True):
        c1, c2 = st.columns(2)
        with c1:
            st.metric("已完成距离", f"{cur_dist}米", f"{dist_pct}%")
            st.progress(dist_pct / 100)
        with c2:
            st.metric("已完成次数", f"{cur_days}次", f"{days_pct}%")
            st.progress(days_pct / 100)

    all_map_list = list(all_maps())
    if "custom_maps" in st.session_state:
        all_map_list.extend(st.session_state.custom_maps)

    if not all_map_list:
        st.info("maps 目录下没有路线文件")
    else:
        sel_name = st.selectbox("选择路线", [m["name"] for m in all_map_list], key="map_sel")
        sel_map = next(m for m in all_map_list if m["name"] == sel_name)
        full_dist = route_distance(sel_map["coords"])
        st.caption(f"路线全长约 {full_dist} 米")

        if "init_dist" not in st.session_state:
            st.session_state.init_dist = random.randint(once_min, once_max)
        init_dist = st.session_state.init_dist
        init_pace = random.uniform(4.0, 7.0)
        init_time = max(1, int(init_dist / (init_pace * 1000 / 3600) / 60))
        init_time = min(init_time, 180)

        c1, c2 = st.columns(2)
        with c1:
            dist = st.number_input("距离(米)", 0, 20000, init_dist, key="run_dist")
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
            st.info("当前使用 OpenStreetMap 预览，效果一般。如需高德地图精确定位，请在项目根目录 .env 文件中设置高德JS API Key")
        map_path = draw_map_folium(track)
        st.iframe(map_path, height=400)

        if AMAP_KEY:
            drawer_url = "http://127.0.0.1:8852/drawer.html"
            st.markdown(
                f'<a href="{drawer_url}" target="_blank" rel="noopener" '
                f'style="display:inline-block;padding:0.4rem 1rem;background:#FF4B4B;color:white;'
                f'border-radius:6px;text-decoration:none;font-size:0.85rem;margin-bottom:0.5rem;">'
                f"轨迹绘制器 (新标签页)</a>",
                unsafe_allow_html=True,
            )

        uploaded = st.file_uploader("加载自定义路线 (JSON)", type=["json"], key="custom_map_upload")
        if uploaded and "last_uploaded" not in st.session_state:
            st.session_state.last_uploaded = None
        if uploaded:
            file_id = f"{uploaded.name}_{uploaded.size}"
            if st.session_state.get("last_uploaded") != file_id:
                st.session_state.last_uploaded = file_id
                try:
                    data = json.loads(uploaded.read())
                    raw = data.get("mapData", [])
                    if raw:
                        pts = []
                        for p in raw:
                            lng, lat = p.split(",")
                            pts.append([float(lat), float(lng)])
                        name = data.get("mapName", uploaded.name)
                        if "custom_maps" not in st.session_state:
                            st.session_state.custom_maps = []
                        cid = f"custom_{len(st.session_state.custom_maps)}_{hash(file_id) % 10000}"
                        st.session_state.custom_maps.append(
                            {"id": cid, "name": f"{name} (自定义)", "coords": pts}
                        )
                        st.success(f"已加载: {name}")
                        st.rerun()
                    else:
                        st.warning("文件中没有轨迹点数据")
                except Exception as e:
                    st.error(f"文件格式错误: {e}")

        ts_base = int(datetime.now().timestamp() * 1000)
        interval = int((duration * 60 * 1000) / max(len(track), 1))
        # track format: lng-lat-timestamp-accuracy (same as Java TrackUtils.getTrackToString)
        pts_str = json.dumps(
            [
                f"{p[1]}-{p[0]}-{ts_base + i * interval}-{random.randrange(5, 10)}"
                for i, p in enumerate(track)
            ],
            ensure_ascii=False,
        )
        year_semester = std.get("semesterYear", "")
        if speed_ok and st.button("提交跑步记录", key="run_submit", type="primary", use_container_width=True):
            r = api_call(
                run.save_run_record_v2,
                distance=dist,
                time=duration,
                track_points=pts_str,
                vocal_status="1",
                record_date=datetime.now().strftime("%Y-%m-%d"),
                year_semester=year_semester,
            )
            if r:
                code = r.get("code")
                if code == 10000:
                    st.success("提交成功")
                    notify("行迹", "跑步记录提交成功")
                    st.session_state.run_info = api_call(run.get_run_info)
                    st.session_state.records = api_call(run.get_run_records, 1, 10)
                    st.session_state.init_dist = random.randint(1000, 6000)
                else:
                    st.error(f"提交失败: {r.get('msg', '未知错误')}")
                    notify("行迹", f"跑步提交失败: {r.get('msg', '未知错误')}")

    # ── Run scheduler ──
    st.divider()
    st.markdown("#### 定时跑步")

    sched_key = "run_sched_enabled"
    if sched_key not in st.session_state:
        st.session_state[sched_key] = load_run_state().get("enabled", False)

    c1, c2 = st.columns([2, 1])
    with c1:
        if st.button(
            "定时跑步 (开启)" if not st.session_state[sched_key]
            else "定时跑步 (关闭)",
            key="run_sched_toggle",
            use_container_width=True,
        ):
            st.session_state[sched_key] = not st.session_state[sched_key]
            cfg = load_run_state()
            cfg["enabled"] = st.session_state[sched_key]
            save_run_state(cfg)
            st.rerun()
    with c2:
        if load_run_state().get("enabled", False):
            st.success("运行中")
        else:
            st.caption("空闲")

    if st.session_state[sched_key]:
        st.warning("此功能需保持程序常驻后台运行，请勿在其它设备登录当前账号")

    with st.expander("定时设置", expanded=st.session_state.get("_run_sched_expand", False)):
        st.session_state._run_sched_expand = True
        run_cfg = load_run_state()

        st.markdown("##### 星期")
        day_names = ["日", "一", "二", "三", "四", "五", "六"]
        day_cols = st.columns(7)
        days = list(run_cfg.get("days", [False]*7))
        for i, (col, name) in enumerate(zip(day_cols, day_names)):
            with col:
                days[i] = st.checkbox(name, value=days[i], key=f"run_day_{i}")

        st.markdown("##### 时间段")
        tr = run_cfg.get("time_ranges", [])
        for i, (start, end) in enumerate(tr):
            c1, c2, c3 = st.columns([2, 2, 1])
            tr[i][0] = c1.text_input("起始", tr[i][0], key=f"run_tr_s{i}")
            tr[i][1] = c2.text_input("结束", tr[i][1], key=f"run_tr_e{i}")
            if c3.button("删除", key=f"run_tr_del{i}"):
                tr.pop(i)
                run_cfg["time_ranges"] = tr
                save_run_state(run_cfg)
                st.rerun()
        if st.button("添加时间段", key="run_tr_add"):
            tr.append(["18:00", "18:30"])
            run_cfg["time_ranges"] = tr
            save_run_state(run_cfg)
            st.rerun()

        st.markdown("##### 路线")
        map_opts = {m["name"]: m["id"] for m in all_maps()}
        if "custom_maps" in st.session_state:
            for m in st.session_state.custom_maps:
                map_opts[m["name"]] = m["id"]
        cur_id = run_cfg.get("map", "")
        cur_idx = 0
        names = list(map_opts.keys())
        for i, n in enumerate(names):
            if map_opts[n] == cur_id:
                cur_idx = i
                break
        sel_name = st.selectbox("选择路线", names, index=cur_idx, key="run_sched_map")

        st.markdown("##### 目标")
        c1, c2 = st.columns(2)
        with c1:
            d_min = st.number_input("最短距离(米)", 0, 10000, run_cfg.get("distance", {}).get("min", 2000), key="run_d_min")
            s_min = st.number_input("最慢配速(km/h)", 1.0, 20.0, run_cfg.get("speed", {}).get("min", 5.0), key="run_s_min", step=0.5)
        with c2:
            d_max = st.number_input("最长距离(米)", 0, 10000, run_cfg.get("distance", {}).get("max", 5000), key="run_d_max")
            s_max = st.number_input("最快配速(km/h)", 1.0, 20.0, run_cfg.get("speed", {}).get("max", 12.0), key="run_s_max", step=0.5)

        if st.button("保存设置", key="run_sched_save", type="primary", use_container_width=True):
            run_cfg["days"] = days
            run_cfg["time_ranges"] = tr
            run_cfg["map"] = map_opts.get(sel_name, "")
            run_cfg["distance"] = {"min": d_min, "max": d_max}
            run_cfg["speed"] = {"min": s_min, "max": s_max}
            save_run_state(run_cfg)
            st.success("设置已保存")

        last = run_cfg.get("last_run")
        if last:
            st.caption(f"上次自动跑步: {last[:16]}")

    st.divider()
    st.markdown("#### 跑步记录")
    if st.button("刷新", use_container_width=True, key="ref_rec"):
        st.session_state.records = api_call(run.get_run_records, 1, 10)
        st.rerun()

    recs2 = st.session_state.records
    rl2 = recs2.get("response") if recs2 else []
    with st.expander(f"跑步记录 ({len(rl2)} 条)", expanded=False):
        if rl2:
            for r in rl2:
                st.markdown(
                    f"<div class='card'><div><b>{r.get('recordDate')}</b> {r.get('defeatedInfo')}</div>"
                    f"<div class='card-sm'>{r.get('runValidDistance')}m | {r.get('runValidTime')}min | {r.get('runSpeed')}m/min</div></div>",
                    unsafe_allow_html=True,
                )
