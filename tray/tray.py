"""系统托盘模块"""
import json
import logging
import os
import threading
import webbrowser

import pystray
from PIL import Image, ImageDraw

logger = logging.getLogger("tray")

_OPEN_URL = "http://localhost:8501"
_STATE_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    ".data", "scheduler.json",
)


def _create_icon_image(size=64):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([22, 4, 42, 24], fill="#FF4B4B")
    draw.polygon([(28, 26), (36, 26), (40, 48), (24, 48)], fill="#FF4B4B")
    draw.polygon([(24, 48), (20, 60), (28, 60), (32, 48)], fill="#FF4B4B")
    draw.polygon([(40, 48), (44, 60), (52, 60), (44, 48)], fill="#FF4B4B")
    draw.polygon([(28, 26), (12, 40), (18, 46), (32, 32)], fill="#FF4B4B")
    draw.polygon([(36, 26), (52, 18), (56, 24), (40, 32)], fill="#FF4B4B")
    return img


def _scheduler_status():
    try:
        with open(_STATE_FILE, encoding="utf-8") as f:
            data = json.load(f)
        return "已开启" if data.get("enabled") else "已关闭"
    except Exception:
        return "未知"


def _open_browser():
    webbrowser.open(_OPEN_URL)


class TrayApp:
    def __init__(self):
        self._thread: threading.Thread | None = None
        self._icon: pystray.Icon | None = None

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        logger.info("tray started")

    def stop(self):
        if self._icon:
            self._icon.stop()
            self._icon = None

    def _run(self):
        image = _create_icon_image()
        menu = pystray.Menu(
            pystray.MenuItem("显示窗口", self._on_show, default=True),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                lambda item: f"定时任务: {_scheduler_status()}",
                lambda: None,
                enabled=False,
            ),
            pystray.MenuItem("退出", self._on_quit),
        )
        self._icon = pystray.Icon("xingji", image, "行迹", menu)
        self._icon.run()

    def _on_show(self):
        _open_browser()

    def _on_quit(self):
        logger.info("tray: quit")
        self._icon.stop()
        self._icon = None
        os._exit(0)
