#!/usr/bin/env python
"""启动 行迹 PaceTrace 前端 + 系统托盘 + 后台定时任务"""
import os
import sys
import threading
import time
from http.server import HTTPServer, SimpleHTTPRequestHandler
from dotenv import load_dotenv

_PDIR = os.path.dirname(os.path.abspath(__file__))
_SRC = os.path.join(_PDIR, "src")
sys.path.insert(0, _PDIR)
sys.path.insert(0, _SRC)
load_dotenv(os.path.join(_PDIR, ".env"))

DRAWER_PORT = 8852


class DrawerHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/drawer.html" or self.path.startswith("/drawer.html"):
            amap_key = os.environ.get("AMAP_KEY", "")
            amap_sec = os.environ.get("AMAP_SECURITY", "")
            drawer_path = os.path.join(_SRC, "frontend", "drawer.html")
            with open(drawer_path, encoding="utf-8") as f:
                html = f.read()
            html = html.replace("{{AMAP_KEY}}", amap_key)
            html = html.replace("{{AMAP_SECURITY}}", amap_sec)
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html.encode("utf-8"))
            return
        return super().do_GET()


def _start_static_server():
    os.chdir(os.path.join(_SRC, "frontend"))
    server = HTTPServer(("127.0.0.1", DRAWER_PORT), DrawerHandler)
    print(f"[static] drawer at http://127.0.0.1:{DRAWER_PORT}/drawer.html")
    server.serve_forever()


def _start_tray():
    try:
        from tray import TrayApp
        t = TrayApp()
        t.start()
    except Exception as e:
        print(f"[tray] {e}")


def _start_scheduler():
    try:
        from scheduler import SignScheduler, load_club_state
        sched = SignScheduler(interval=60)
        while True:
            state = load_club_state()
            if state.get("enabled", False):
                if not sched.running:
                    print("[scheduler] club: starting...")
                    sched.start()
            else:
                if sched.running:
                    print("[scheduler] club: stopping...")
                    sched.stop()
            time.sleep(10)
    except Exception as e:
        print(f"[scheduler] club error: {e}")


def _start_run_scheduler():
    try:
        from scheduler import RunScheduler, load_run_state
        sched = RunScheduler(interval=120)
        while True:
            state = load_run_state()
            if state.get("enabled", False):
                if not sched.running:
                    print("[scheduler] run: starting...")
                    sched.start()
            else:
                if sched.running:
                    print("[scheduler] run: stopping...")
                    sched.stop()
            time.sleep(10)
    except Exception as e:
        print(f"[scheduler] run error: {e}")


if __name__ == "__main__":
    threading.Thread(target=_start_static_server, daemon=True).start()
    threading.Thread(target=_start_tray, daemon=True).start()
    threading.Thread(target=_start_scheduler, daemon=True).start()
    threading.Thread(target=_start_run_scheduler, daemon=True).start()

    app = os.path.join(_SRC, "frontend", "app.py")
    os.system(f"streamlit run \"{app}\"")

    print("[scheduler] web ui closed, scheduler keeps running in background")
    print("[scheduler] press Ctrl+C or use tray menu to exit")
    while True:
        time.sleep(60)
