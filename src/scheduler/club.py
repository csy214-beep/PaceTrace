"""定时签到/签退任务（修复版）"""

import json
import logging
import os
import threading
import time
from datetime import datetime, timedelta

from lib.geo import random_point
from lib.time import parse_time
from tray.tray import notify, update_menu as _update_menu

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".data")
STATE_FILE = os.path.join(DATA_DIR, "scheduler_club.json")
logger = logging.getLogger("scheduler")
_lock = threading.Lock()


# ── 持久化状态 ──────────────────────────────────────────────
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


# ── 工具函数 ────────────────────────────────────────────────
def _activity_window(data: dict) -> tuple[datetime | None, datetime | None]:
    """
    从 API 返回的 data 中提取活动窗口。
    时间格式可能为：
      - '2026-05-12 18:00:00'
      - '2026-05-12 18:00'
      - '18:00'
    若 startTime/endTime 均为当天的纯时间且 end 表示次日凌晨（< start），
    则自动将 end 加一天。
    返回 (window_start - 10min, window_end + 10min)
    """
    st = data.get("startTime") or data.get("start_time")
    et = data.get("endTime") or data.get("end_time")
    start = parse_time(st) if st else None
    end = parse_time(et) if et else None
    # 跨天修正：如果 end < start（例如 start=22:00, end=02:00）
    if start and end and end < start:
        end += timedelta(days=1)
    # 窗口前后各延长 10 分钟作为缓冲
    if start:
        start = start - timedelta(minutes=10)
    if end:
        end = end + timedelta(minutes=10)
    return start, end


# ── 调度器主体 ──────────────────────────────────────────────
class SignScheduler:
    """定时签到/签退任务，以独立守护线程运行"""

    def __init__(self, interval: int = 60):
        self.interval = interval  # 活动窗口内轮询间隔（秒）
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()

    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    # ── 启动 / 停止 ────────────────────────────────────────
    def start(self):
        if self.running:
            logger.warning("scheduler already running")
            return
        self._stop.clear()
        self._thread = threading.Thread(
            target=self._run, daemon=True, name="sign-scheduler"
        )
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
            if self._thread.is_alive():
                logger.warning(
                    "scheduler thread did not stop in time, will be abandoned"
                )
            self._thread = None
        state = load_state()
        state["enabled"] = False
        save_state(state)
        notify("行迹", "自动签到/签退已关闭")
        _update_menu()
        logger.info("scheduler stopped")

    # ── 可中断休眠 ─────────────────────────────────────────
    def _sleep(self, seconds: float):
        """可被 stop() 立即中断的休眠"""
        if seconds > 0:
            self._stop.wait(timeout=seconds)

    def _sleep_until(self, dt: datetime):
        """休眠直到 dt 时间点，期间可被中断"""
        while not self._stop.is_set():
            now = datetime.now()
            if now >= dt:
                break
            wait_sec = (dt - now).total_seconds()
            if wait_sec > 0:
                self._sleep(wait_sec)

    # ── 等待活动窗口 ──────────────────────────────────────
    def _get_sign_in_data(self):
        """获取签到状态数据，异常时返回 None，顺便缓存场地坐标供签退回退"""
        from api.club import get_sign_in_tf

        try:
            resp = get_sign_in_tf()
            if resp and resp.get("code") == 10000:
                data = resp.get("response") or {}
                if data.get("latitude") and data.get("longitude"):
                    state = load_state()
                    state["last_lat"] = data["latitude"]
                    state["last_lng"] = data["longitude"]
                    if data.get("activityId"):
                        state["last_aid"] = data["activityId"]
                    save_state(state)
                return data
        except Exception as e:
            logger.error("get_sign_in_tf error: %s", e)
        return None

    def _wait_until_window(self):
        """
        循环查询活动窗口时间，直到当前时间处于窗口内。
        窗口未开始 → 休眠到开始时间
        窗口已结束 → 休眠 1 小时再查（可中断）
        API 异常 → 退避最多 2 分钟后再试
        """
        while not self._stop.is_set():
            data = self._get_sign_in_data()
            if not data:
                # API 异常，退避时间不超过 1 分钟
                logger.info("cannot get activity window, retry in 60s")
                self._sleep(60)
                continue

            ws, we = _activity_window(data)
            now = datetime.now()
            if ws and now < ws:
                logger.info("activity not started yet, sleep until %s", ws)
                self._sleep_until(ws)
                continue
            if we and now > we:
                logger.info("activity window ended (now=%s, end=%s), sleep 1h", now, we)
                self._sleep(3600)
                continue
            # 在窗口内
            logger.info(
                "inside activity window (now=%s, start=%s, end=%s)", now, ws, we
            )
            return

    # ── 主循环 ─────────────────────────────────────────────
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
            self._sleep(self.interval)

    # ── 单次签到/签退动作 ──────────────────────────────────
    def _tick(self):
        from api.club import get_sign_in_tf, sign_in_or_back

        resp = get_sign_in_tf()
        if not resp or resp.get("code") != 10000:
            logger.info("tick: get_sign_in_tf failed or unauthorized")
            return
        data = resp.get("response")
        if not data:
            return

        status = str(data.get("signStatus", ""))
        aid = data.get("activityId")
        lat = data.get("latitude")
        lng = data.get("longitude")

        # 如果 API 未返回坐标，尝试用上次缓存的场地坐标回退
        if not lat or not lng:
            state = load_state()
            lat = state.get("last_lat")
            lng = state.get("last_lng")
            if not aid:
                aid = state.get("last_aid")
            if lat and lng:
                logger.warning("tick: API missing coords, falling back to cached (lat=%s lng=%s)", lat, lng)
            else:
                logger.info("tick: missing data and no cached coords (aid=%s)", aid)
                return

        if not aid:
            logger.info("tick: missing activityId and no cached fallback")
            return

        lat_r, lng_r = random_point(lat, lng, 100)

        if status == "0":
            # 未签到 → 签到
            r = sign_in_or_back(aid, lat_r, lng_r, "1")
            msg = r.get("msg", "?") if r else "no response"
            if r and r.get("code") == 10000:
                logger.info("auto sign-in OK (activity=%s)", aid)
                notify("行迹", f"自动签到成功: {data.get('activityName', aid)}")
            else:
                logger.info("auto sign-in failed: %s", msg)
                notify("行迹", f"自动签到失败: {msg}")
        elif status == "1":
            # 已签到 → 签退
            r = sign_in_or_back(aid, lat_r, lng_r, "2")
            msg = r.get("msg", "?") if r else "no response"
            if r and r.get("code") == 10000:
                logger.info("auto sign-back OK (activity=%s)", aid)
                notify("行迹", f"自动签退成功: {data.get('activityName', aid)}")
            else:
                logger.info("auto sign-back failed: %s", msg)
                notify("行迹", f"自动签退失败: {msg}")
        else:
            logger.info("unknown signStatus=%s, skipping", status)
