import json
import os
import math
import random
import tempfile
from datetime import datetime, date, timedelta

import streamlit as st
import folium

from api import auth, run, club
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


MAPS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "maps")
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
        a, b = coords[i - 1], coords[i]
        dx = (b[1] - a[1]) * 111320 * math.cos(math.radians((a[0] + b[0]) / 2))
        dy = (b[0] - a[0]) * 111320
        d += math.sqrt(dx * dx + dy * dy)
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


def random_point_nearby(lat, lng, radius=100):
    angle = random.random() * 2 * math.pi
    r = math.sqrt(random.random()) * radius
    dx = r * math.cos(angle) / (111320 * math.cos(math.radians(float(lat))))
    dy = r * math.sin(angle) / 111320
    return str(float(lat) + dy), str(float(lng) + dx)


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
