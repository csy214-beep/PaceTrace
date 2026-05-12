# PaceTrace

A campus run management dashboard with club activity support, auto sign-in scheduler, and an AMap-based track drawer.

## Features

- **Authentication** — login with phone number and password; token persists locally.
- **Dashboard** — overview of run stats (valid days, distance, pace) and recent records.
- **Campus Run** — select a route from built-in maps, set distance and duration, preview the track on a map, and submit run records.
- **Club Activities** — browse semester projects, register/cancel activities, sign in/back with GPS check-in.
- **Auto Sign-In/Back** — background scheduler that detects activity time windows and performs sign-in/back automatically at the right moment.
- **Track Drawer** *(requires AMap key)* — a standalone browser-based tool for drawing custom running routes on an AMap-powered map. Supports continuous freehand drawing, single-point placement, undo, export/import JSON files.
- **System Tray** — background tray icon showing scheduler status, with quick launch and exit.
- **Operation Log** — all API requests and scheduler actions are logged locally to `.data/app.log`.

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
python -m venv .venv          # skip if already exists
.venv\Scripts\activate        # or source .venv/bin/activate
pip install -r requirements.txt --upgrade
```

## Configuration

Copy `.env.example` to `.env` and fill in your AMap credentials (optional, required for map preview and track drawer):

```
AMAP_KEY=your_amap_js_api_key
AMAP_SECURITY=your_amap_security_code
```

## Project Structure

```
.
├── api/              # API client library
├── frontend/         # Streamlit web UI
├── scheduler/        # Background scheduler module
├── tray/             # System tray module
├── maps/             # Built-in route data (JSON)
├── .data/            # Local data (token, user, logs)
├── run.py            # Application entry point
└── .env              # Environment configuration
```

## Thanks

- maps from yanyaoli/byerun-web and the repo's contributors. (CC BY-NC 4.0)
- core idea from <https://www.jysafe.cn/4707.air>
- coding by opencode.

## License

[CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/)
