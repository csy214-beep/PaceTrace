# PaceTrace

A campus run management dashboard with club activity support, auto sign-in/run schedulers, and an AMap-based track drawer.

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
git clone https://github.com/csy214-beep/PaceTrace.git
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

## License

[CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/)
