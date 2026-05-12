"""定时签到/签退任务"""
import json
import logging
import math
import os
import random
import threading
from datetime import datetime, timedelta

from tray.tray import notify, update_menu as _update_menu

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".data")
STATE_FILE = os.path.join(DATA_DIR, "scheduler.json")
logger = logging.getLogger("scheduler")
_lock = threading.Lock()


def load_state() -> dict:
    with _lock:
        os.makedirs(DATA_DIR, exist_ok=True)
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"enabled": False}


def save_state(state: dict):
    with _lock:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f)


def _random_point(lat: str, lng: str, radius: float = 100):
    angle = random.random() * 2 * math.pi
    r = math.sqrt(random.random()) * radius
    dx = r * math.cos(angle) / (111320 * math.cos(math.radians(float(lat))))
    dy = r * math.sin(angle) / 111320
    return str(float(lat) + dy), str(float(lng) + dx)


def _parse_time(t: str) -> datetime | None:
    """解析 '2026-05-12 18:00:00' 或 '18:00' 格式"""
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%H:%M"):
        try:
            return datetime.strptime(t, fmt)
        except ValueError:
            continue
    return None


def _activity_window(data: dict) -> tuple[datetime | None, datetime | None]:
    """返回 (window_start, window_end)，None 表示不限"""
    st = data.get("startTime")
    et = data.get("endTime")
    start = _parse_time(st) if st else None
    end = _parse_time(et) if et else None
    if start:
        start = start - timedelta(minutes=10)
    if end:
        end = end + timedelta(minutes=10)
    return start, end


def _sleep_until(dt: datetime):
    """阻塞直到指定时间"""
    now = datetime.now()
    secs = (dt - now).total_seconds()
    if secs > 0:
        logger.info("sleeping %.0f seconds until activity window", secs)
        threading.Event().wait(secs)


class SignScheduler:
    """定时签到/签退任务，以独立线程运行"""

    def __init__(self, interval: int = 60):
        self.interval = interval
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()

    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self):
        if self.running:
            logger.warning("scheduler already running")
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        state = load_state()
        state["enabled"] = True
        save_state(state)
        notify("行迹", "自动签到/签退已开启")
        _update_menu()
        logger.info("scheduler started")

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=5)
            self._thread = None
        state = load_state()
        state["enabled"] = False
        save_state(state)
        notify("行迹", "自动签到/签退已关闭")
        _update_menu()
        logger.info("scheduler stopped")

    def _wait_until_window(self):
        """查询活动时间窗口，等待到窗口开启"""
        from api.club import get_sign_in_tf

        while not self._stop.is_set():
            resp = get_sign_in_tf()
            if resp and resp.get("code") == 10000:
                data = resp.get("response") or {}
                ws, we = _activity_window(data)
                now = datetime.now()
                if ws and now < ws:
                    _sleep_until(ws)
                    continue
                if we and now > we:
                    logger.info("activity window ended, sleeping 1h")
                    _sleep_until(now + timedelta(hours=1))
                    continue
                return
            self._stop.wait(60)

    def _run(self):
        logger.info("scheduler loop started")
        while not self._stop.is_set():
            self._wait_until_window()
            if self._stop.is_set():
                break
            try:
                self._tick()
            except Exception as e:
                logger.error("tick error: %s", e)
            self._stop.wait(self.interval)

    def _tick(self):
        from api.club import get_sign_in_tf, sign_in_or_back
        from tray.tray import notify

        resp = get_sign_in_tf()
        if not resp or resp.get("code") != 10000:
            return
        data = resp.get("response")
        if not data:
            return

        status = data.get("signStatus")
        aid = data.get("activityId")
        lat = data.get("latitude")
        lng = data.get("longitude")

        if not aid or not lat or not lng:
            logger.info("tick: missing data (aid=%s lat=%s lng=%s)", aid, lat, lng)
            return

        lat_r, lng_r = _random_point(lat, lng, 100)

        if status == "0":
            r = sign_in_or_back(aid, lat_r, lng_r, "1")
            msg = r.get("msg", "?") if r else "no response"
            if r and r.get("code") == 10000:
                logger.info("auto sign-in OK (activity=%s)", aid)
                notify("行迹", f"自动签到成功: {data.get('activityName', aid)}")
            else:
                logger.info("auto sign-in failed: %s", msg)
                notify("行迹", f"自动签到失败: {msg}")
        elif status == "1":
            r = sign_in_or_back(aid, lat_r, lng_r, "2")
            msg = r.get("msg", "?") if r else "no response"
            if r and r.get("code") == 10000:
                logger.info("auto sign-back OK (activity=%s)", aid)
                notify("行迹", f"自动签退成功: {data.get('activityName', aid)}")
            else:
                logger.info("auto sign-back failed: %s", msg)
                notify("行迹", f"自动签退失败: {msg}")
