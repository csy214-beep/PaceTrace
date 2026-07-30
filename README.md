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

### Using uv (recommended)

```bash
git clone https://github.com/igugyj/PaceTrace.git
cd PaceTrace
uv sync
uv run python run.py
```

### Using pip

```bash
git clone https://github.com/igugyj/PaceTrace.git
cd PaceTrace
python -m venv .venv
.venv\Scripts\activate         # Windows
# source .venv/bin/activate    # Linux / macOS
pip install -r requirements.txt
python run.py
```

### Using the launcher (Windows only)

Build `launcher/launcher.exe` (see `launcher/README.md`) and run it — guides through cloning, dependency installation, and launch.

Open `http://localhost:8501` in your browser.

### Update

```bash
git pull origin main
uv sync
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
├── launcher/         # Windows setup tool (C++, single-file exe)
├── run.py            # Application entry point
├── .env              # Environment configuration
└── requirements.txt
```

## Thanks

- maps from [yanyaoli/byerun-web](https://github.com/yanyaoli/byerun-web) _([CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/))_ and the repo's contributors.
- core idea from <https://www.jysafe.cn/4707.air>
- coding by opencode(DeepSeek v4 flash), claude(Sonnet 4.6), DeepSeek v4.

## License

[CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/)
