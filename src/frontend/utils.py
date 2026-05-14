import os
import tempfile
from datetime import datetime, date, timedelta

import streamlit as st
import folium

from api import auth
from lib.geo import random_point
from lib.maps import load_maps
from frontend.logger import logger


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


AMAP_KEY = os.environ.get("AMAP_KEY", "")

_all_maps_cache = None


def all_maps():
    global _all_maps_cache
    if _all_maps_cache is None:
        _all_maps_cache = load_maps()
    return _all_maps_cache


def draw_map_folium(coords):
    lat0 = sum(c[0] for c in coords) / len(coords)
    lng0 = sum(c[1] for c in coords) / len(coords)
    if AMAP_KEY:
        tiles = f"https://webrd01.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={{x}}&y={{y}}&z={{z}}&key={AMAP_KEY}"
        attr = "AMap"
    else:
        tiles = "OpenStreetMap"
        attr = "OSM"
    m = folium.Map(location=[lat0, lng0], zoom_start=16, tiles=tiles, attr=attr, control_scale=True, zoom_control=False)
    folium.PolyLine(coords, color="#FF4B4B", weight=3, opacity=0.85).add_to(m)
    folium.CircleMarker(coords[0], radius=5, color="#FF4B4B", fill=True).add_to(m)
    folium.CircleMarker(coords[-1], radius=5, color="#FF4B4B", fill=True).add_to(m)
    tmp = tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w", encoding="utf-8")
    tmp.write(m.get_root().render())
    tmp.close()
    return tmp.name


def parse_activity_time(mmdd: str, time_str: str) -> datetime | None:
    if not time_str:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(time_str, fmt)
        except ValueError:
            continue
    try:
        t = datetime.strptime(time_str, "%H:%M").time()
        if not mmdd:
            return None
        month, day = map(int, mmdd.split("-"))
        year = date.today().year
        return datetime(year, month, day, t.hour, t.minute)
    except (ValueError, TypeError):
        return None


def get_activity_window(mmdd: str, start_str: str, end_str: str) -> tuple[datetime | None, datetime | None]:
    start_dt = parse_activity_time(mmdd, start_str)
    end_dt = parse_activity_time(mmdd, end_str)
    if start_dt and end_dt and end_dt < start_dt:
        end_dt += timedelta(days=1)
    return start_dt, end_dt
