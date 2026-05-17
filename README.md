# PaceTrace

![GitHub Repo stars](https://img.shields.io/github/stars/igugyj/PaceTrace?style=social)
![GitHub forks](https://img.shields.io/github/forks/igugyj/PaceTrace?style=social)
![GitHub issues](https://img.shields.io/github/issues/igugyj/PaceTrace?style=social)
[![Sync to Gitee](https://github.com/igugyj/PaceTrace/actions/workflows/sync-to-gitee.yml/badge.svg?branch=main)](https://github.com/igugyj/PaceTrace/actions/workflows/sync-to-gitee.yml)

A campus run management dashboard with club activity support, auto sign-in/run schedulers, and an AMap-based track drawer.

> Android app available on [igugyj/PaceTraceKotlin](https://github.com/igugyj/PaceTraceKotlin)

## Features

- **Authentication** — login with phone number and password; token persists locally.
- **Dashboard** — overview of run stats (valid days, distance, pace) and recent records.
- **Campus Run** — select a route from built-in maps, set distance and duration, preview the track on a map, submit run records, and view history.
- **Auto Run Scheduler** — schedule automatic run submissions by day of week, time range, route, distance, and pace range.
- **Club Activities** — browse semester projects, register/cancel activities, sign in/back with GPS check-in.
- **Auto Sign-In/Back** — background scheduler that detects activity time windows and performs sign-in/back automatically.
- **Track Drawer** *(requires AMap key)* — standalone browser-based tool for drawing custom running routes on an AMap map. Supports continuous freehand and single-point drawing, undo, path length display, and JSON export/import.
- **System Tray** — background tray icon showing scheduler status, with quick launch and exit.
- **Operation Log** — all API requests and scheduler actions logged to `.data/app.log`.

## Quick Start

```bash
git clone https://github.com/igugyj/PaceTrace.git
cd PaceTrace
python -m venv .venv
# source .venv/bin/activate    # Linux / macOS
.venv\Scripts\activate         # Windows
pip install -r requirements.txt
python run.py
```

Open `http://localhost:8501` in your browser.

### Update

```bash
git pull origin main
.venv\Scripts\activate        # or source .venv/bin/activate
pip install -r requirements.txt --upgrade
```

## Configuration

Copy `.env.example` to `.env` and fill in your credentials:

```
APPKEY=your_api_appkey
APPSECRET=your_api_secret
BASE_URL=https://run-lb.tanmasports.com/
UA=okhttp/3.10.0
AMAP_KEY=your_amap_js_api_key
AMAP_SECURITY=your_amap_security_code
```

## Project Structure

```
.
├── .data/            # Local data (token, user, logs, scheduler states)
├── src/
│   ├── api/          # API client library
│   ├── frontend/     # Streamlit web UI (pages, utils, styles)
│   ├── maps/         # Built-in route data (JSON)
│   ├── scheduler/    # Background scheduler (club + run)
│   └── tray/         # System tray module
├── scripts/          # Startup scripts (bat/sh)
├── run.py            # Application entry point
├── .env              # Environment configuration
└── requirements.txt
```

## Dependencies

| Library | Version | License | Purpose |
|---------|---------|---------|---------|
| streamlit | 1.57.0 | Apache 2.0 | Web UI framework |
| requests | 2.34.1 | Apache 2.0 | HTTP client for API calls |
| folium | 0.20.0 | MIT | Interactive route maps |
| pystray | 0.19.5 | LGPL-3.0 | System tray icon |
| Pillow | 12.2.0 | Historical | Tray icon rendering |
| python-dotenv | 1.2.2 | BSD 3-Clause | Environment config loading |

This project is subject to the terms of all above licenses.

## Thanks

- maps from yanyaoli/byerun-web([CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/)) and the repo's contributors.
- core idea from <https://www.jysafe.cn/4707.air>
- coding by opencode(DeepSeek v4 flash), claude(Sonnet 4.6), DeepSeek v4.

## License

[CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/)
