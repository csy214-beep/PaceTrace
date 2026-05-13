"""定时跑步任务

数据结构 (.data/scheduler_run.json):
{
  "enabled": bool,
  "days": [bool x7],        # 周日至周六
  "time_ranges": [["HH:MM","HH:MM"], ...],
  "map": "map_id",
  "distance": {"min": int, "max": int},
  "speed": {"min": float, "max": float},
  "last_run": str | null
}
"""
import json
import logging
import math
import os
import random
import threading
from datetime import datetime, date

from tray.tray import notify, update_menu as _update_menu

logger = logging.getLogger("run_sched")

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".data")
STATE_FILE = os.path.join(DATA_DIR, "scheduler_run.json")
_lock = threading.Lock()


def load() -> dict:
    with _lock:
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            "enabled": False,
            "days": [False]*7,
            "time_ranges": [],
            "map": "",
            "distance": {"min": 2000, "max": 5000},
            "speed": {"min": 5.0, "max": 12.0},
            "last_run": None,
        }


def save(state: dict):
    with _lock:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False)


def _route_distance(coords):
    d = 0
    for i in range(1, len(coords)):
        a, b = coords[i-1], coords[i]
        dx = (b[1] - a[1]) * 111320 * math.cos(math.radians((a[0] + b[0]) / 2))
        dy = (b[0] - a[0]) * 111320
        d += math.sqrt(dx*dx + dy*dy)
    return int(d)


def _build_track(coords, target_dist):
    full_d = _route_distance(coords)
    if full_d <= 0:
        return coords
    n = len(coords)
    start = random.randint(0, n - 1)
    result = []
    i = start
    while _route_distance(result) < target_dist:
        result.append(coords[i])
        i = (i + 1) % n
    return result


def _random_point(lat, lng, radius=100):
    angle = random.random() * 2 * math.pi
    r = math.sqrt(random.random()) * radius
    dx = r * math.cos(angle) / (111320 * math.cos(math.radians(float(lat))))
    dy = r * math.sin(angle) / 111320
    return str(float(lat) + dy), str(float(lng) + dx)


def _parse_time(t: str) -> datetime | None:
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%H:%M"):
        try:
            return datetime.strptime(t, fmt)
        except ValueError:
            continue
    return None


def _load_maps():
    """Load maps without depending on frontend modules."""
    maps_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "src", "maps")
    items = []
    if not os.path.isdir(maps_dir):
        return items
    for f in sorted(os.listdir(maps_dir)):
        if not f.endswith(".json"):
            continue
        try:
            with open(os.path.join(maps_dir, f), encoding="utf-8") as fh:
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


class RunScheduler:
    def __init__(self, interval: int = 120):
        self.interval = interval
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()

    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self):
        if self.running:
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        s = load()
        s["enabled"] = True
        save(s)
        notify("行迹", "定时跑步已开启")
        _update_menu()
        logger.info("run scheduler started")

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=5)
            self._thread = None
        s = load()
        s["enabled"] = False
        save(s)
        notify("行迹", "定时跑步已关闭")
        _update_menu()
        logger.info("run scheduler stopped")

    def _run(self):
        logger.info("run scheduler loop started")
        while not self._stop.is_set():
            try:
                self._tick()
            except Exception as e:
                logger.error("run tick error: %s", e)
            self._stop.wait(self.interval)

    def _in_window(self, cfg: dict) -> bool:
        """Check if current time matches schedule."""
        now = datetime.now()
        dow = now.weekday()  # 0=Mon
        days = cfg.get("days", [False]*7)
        # convert Mon=0 to Sun=0 index in our list [Sun..Sat]
        idx = (dow + 1) % 7
        if not days[idx]:
            return False
        time_str = now.strftime("%H:%M")
        for tr in cfg.get("time_ranges", []):
            if len(tr) == 2 and tr[0] <= time_str <= tr[1]:
                return True
        return False

    def _tick(self):
        from api.run import get_run_info, save_run_record_v2

        cfg = load()
        if not cfg.get("enabled"):
            return
        if not self._in_window(cfg):
            return

        # load maps directly
        maps = _load_maps()
        if not maps:
            logger.info("run tick: no maps available")
            return

        # pick map
        map_id = cfg.get("map", "")
        sel = None
        for m in maps:
            if m["id"] == map_id:
                sel = m
                break
        if not sel and maps:
            sel = maps[0]
        if not sel:
            return

        # distance + speed
        d_min = cfg.get("distance", {}).get("min", 2000)
        d_max = cfg.get("distance", {}).get("max", 5000)
        s_min = cfg.get("speed", {}).get("min", 5.0)
        s_max = cfg.get("speed", {}).get("max", 12.0)

        dist = random.randint(d_min, d_max)
        speed = random.uniform(s_min, s_max)
        dur = max(1, int(dist / (speed * 1000 / 3600) / 60))

        track = _build_track(sel["coords"], dist)
        pts_str = json.dumps(
            [f"{p[1]}-{p[0]}-{int(datetime.now().timestamp()*1000) + i*int(dur*60*1000/max(len(track),1))}-{round(random.uniform(3,15),1)}"
             for i, p in enumerate(track)],
            ensure_ascii=False,
        )

        resp = save_run_record_v2(
            distance=dist, time=dur,
            track_points=pts_str, vocal_status="1",
            record_date=datetime.now().strftime("%Y-%m-%d"),
        )

        if resp and resp.get("code") == 10000:
            logger.info("run auto OK: distance=%dm time=%dmin speed=%.1f", dist, dur, speed)
            notify("行迹", f"自动跑步完成: {dist}m {dur}min")
            s = load()
            s["last_run"] = datetime.now().isoformat()
            save(s)
        else:
            msg = resp.get("msg", "?") if resp else "no response"
            logger.info("run auto failed: %s", msg)
            notify("行迹", f"自动跑步失败: {msg}")
