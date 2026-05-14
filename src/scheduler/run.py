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
import os
import random
import threading
from datetime import datetime

from lib.geo import route_distance, build_track
from lib.maps import load_maps
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
            "last_run_date": None,
        }


def save(state: dict):
    with _lock:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False)





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
        from api.run import get_run_info, get_run_standard, save_run_record_v2

        cfg = load()
        if not cfg.get("enabled"):
            return
        if not self._in_window(cfg):
            return

        # daily limit: max 1 run per day
        today = datetime.now().strftime("%Y-%m-%d")
        if cfg.get("last_run_date") == today:
            logger.debug("tick: already ran today (%s), skip", today)
            return

        # load maps directly
        maps = load_maps()
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

        # fetch year_semester from run standard dynamically (matching Java behavior)
        std_resp = get_run_standard()
        std = std_resp.get("response") or {}
        year_semester = std.get("semesterYear") or ""

        # distance + speed
        d_min = cfg.get("distance", {}).get("min", 2000)
        d_max = cfg.get("distance", {}).get("max", 5000)
        s_min = cfg.get("speed", {}).get("min", 5.0)
        s_max = cfg.get("speed", {}).get("max", 12.0)

        dist = random.randint(d_min, d_max)
        speed = random.uniform(s_min, s_max)
        dur = max(1, int(dist / (speed * 1000 / 3600) / 60))

        track = build_track(sel["coords"], dist)
        # track format: lng-lat-timestamp-accuracy (same as Java TrackUtils.getTrackToString)
        pts_str = json.dumps(
            [f"{p[1]}-{p[0]}-{int(datetime.now().timestamp()*1000) + i*int(dur*60*1000/max(len(track),1))}-{random.randrange(5, 10)}"
             for i, p in enumerate(track)],
            ensure_ascii=False,
        )

        resp = save_run_record_v2(
            distance=dist, time=dur,
            track_points=pts_str, vocal_status="1",
            record_date=datetime.now().strftime("%Y-%m-%d"),
            year_semester=year_semester,
        )

        if resp and resp.get("code") == 10000:
            logger.info("run auto OK: distance=%dm time=%dmin speed=%.1f", dist, dur, speed)
            notify("行迹", f"自动跑步完成: {dist}m {dur}min")
            from api.context import ctx
            s = load()
            s["last_run"] = datetime.now().isoformat()
            s["last_run_date"] = today
            s["last_student_id"] = ctx.user.studentId
            save(s)
        else:
            msg = resp.get("msg", "?") if resp else "no response"
            logger.info("run auto failed: %s", msg)
            notify("行迹", f"自动跑步失败: {msg}")
