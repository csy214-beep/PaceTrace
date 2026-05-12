#!/usr/bin/env python
"""启动 行迹 PaceTrace 前端 + 系统托盘 + 后台定时任务"""
import os
import sys
import threading
import time

_PDIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _PDIR)


def _start_tray():
    try:
        from tray import TrayApp
        t = TrayApp()
        t.start()
    except Exception as e:
        print(f"[tray] {e}")


def _start_scheduler():
    try:
        from scheduler import SignScheduler, load_state
        sched = SignScheduler(interval=60)
        while True:
            state = load_state()
            if state.get("enabled", False):
                if not sched.running:
                    print("[scheduler] starting...")
                    sched.start()
            else:
                if sched.running:
                    print("[scheduler] stopping...")
                    sched.stop()
            time.sleep(10)
    except Exception as e:
        print(f"[scheduler] {e}")


if __name__ == "__main__":
    threading.Thread(target=_start_tray, daemon=True).start()
    threading.Thread(target=_start_scheduler, daemon=True).start()

    app = os.path.join(_PDIR, "frontend", "app.py")
    os.system(f"streamlit run \"{app}\"")

    # keep scheduler alive after web page closes
    print("[scheduler] web ui closed, scheduler keeps running in background")
    print("[scheduler] press Ctrl+C or use tray menu to exit")
    while True:
        time.sleep(60)
