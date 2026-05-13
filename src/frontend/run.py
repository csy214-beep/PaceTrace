import json
import random
from datetime import datetime

import streamlit as st

from api import run
from frontend.utils import (
    api_call,
    all_maps,
    route_distance,
    build_track,
    draw_map_folium,
    AMAP_KEY,
)
from tray.tray import notify


def show_run_page():
    if not all_maps:
        st.info("maps 目录下没有路线文件")
    else:
        all_map_list = list(all_maps)
        if "custom_maps" in st.session_state:
            all_map_list.extend(st.session_state.custom_maps)
        sel_name = st.selectbox("选择路线", [m["name"] for m in all_map_list], key="map_sel")
        sel_map = next(m for m in all_map_list if m["name"] == sel_name)
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
        pts_str = json.dumps(
            [
                f"{p[1]}-{p[0]}-{ts_base + i * interval}-{round(random.uniform(3, 15), 1)}"
                for i, p in enumerate(track)
            ],
            ensure_ascii=False,
        )
        if speed_ok and st.button("提交跑步记录", key="run_submit", type="primary", use_container_width=True):
            r = api_call(
                run.save_run_record_v2,
                distance=dist,
                time=duration,
                track_points=pts_str,
                vocal_status="1",
                record_date=datetime.now().strftime("%Y-%m-%d"),
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

    st.divider()
    st.markdown("#### 跑步记录")
    if st.button("刷新", use_container_width=True, key="ref_rec"):
        st.session_state.records = api_call(run.get_run_records, 1, 10)
        st.rerun()
    recs2 = st.session_state.records
    rl2 = recs2.get("response") if recs2 else []
    if rl2:
        for r in rl2:
            st.markdown(
                f"<div class='card'><div><b>{r.get('recordDate')}</b> {r.get('defeatedInfo')}</div>"
                f"<div class='card-sm'>{r.get('runValidDistance')}m | {r.get('runValidTime')}min | {r.get('runSpeed')}m/min</div></div>",
                unsafe_allow_html=True,
            )
