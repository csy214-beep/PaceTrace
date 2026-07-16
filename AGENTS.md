# PaceTrace — Agent Guide

## Quick start

```bash
uv sync
uv run python run.py  # Streamlit UI + tray + 2 scheduler watchdog threads
```

Python >=3.13 required. Or use `launcher/launcher.exe` (build from `launcher/`) for a guided install.

## Build the C++ launcher

```bash
cmake -B build -G "MinGW Makefiles" -DCMAKE_MAKE_PROGRAM=D:/software/gcc/bin/make.exe launcher/
cmake --build build
# Output: build/launcher.exe (single file, zero external DLLs)
```

## Startup flow

`run.py` starts 4 daemon threads (static drawer server :8852, system tray, club scheduler watchdog, run scheduler watchdog), then launches Streamlit via `streamlit.web.cli.main()`. After browser closes, schedulers keep running; Ctrl+C or tray exit kills process. Streamlit entrypoint: `src/frontend/app.py`.

## API signing

`src/api/client.py` — every request signed via `_build_sign()`:
1. Sort query params alphabetically, flatten `k=v` (skip empty values)
2. Concatenate: `k1v1k2v2...` + `APPKEY` + `APPSECRET` + (compact JSON body if POST/PUT/PATCH)
3. MD5 of above, uppercase → `sign` header

Env vars `APPKEY`, `APPSECRET`, `BASE_URL`, `UA` read at **api module import time** via `os.environ[]` — must be set before `from api import ...`. `run.py` loads `.env` via `python-dotenv`. `test.py` and `frontend/app.py` parse `.env` manually.

## Auth

`auth.login(phone, password)` → MD5(lowercase) hash password, POST `v1/auth/login/password` with device spoof (Xiaomi/Mi 10/Android 12, appVersions 1.8.5). Token saved to `.data/.token`; user dict to `.data/.user`. `ctx` singleton (`src/api/context.py`) holds `User` and `RunStandard`. Token expiry (code `30005`) caught in frontend's `api_call()` wrapper (forces re-login) but **not** caught by schedulers.

## Run submission

Active endpoint: `save_run_record_v2` → POST `v1/unirun/save/run/record/new`.

| Field | Note |
|---|---|
| `yearSemester` | MUST fetch from `get_run_standard().semesterYear` — never hardcode |
| `trackPoints` | JSON array of `"lng-lat-timestamp-accuracy"` strings. Timestamps in **milliseconds**, accuracy random 5–10m |
| `runTime` / `runDistance` | Duration in minutes, distance in meters |
| Device spoof | Same as login (Xiaomi, Mi 10, Android 12, appVersions 1.8.5) |
| `innerSchool` | Always `"1"` |

Track builder in `src/lib/geo.py`: `build_track(route_coords, target_distance)` → evenly spaced points. Route coords from `src/maps/*.json` (GCJ-02 高德坐标系 — not WGS-84).

## Club sign-in/back

1. `club.get_sign_in_tf()` returns venue lat/lng, activity window, `signStatus`
2. `signStatus == "0"` → POST sign-in (`signType: "1"`); `"1"` → sign-back (`signType: "2"`)
3. Coordinates offset ~100m via `lib.geo.random_point()`
4. Cross-day windows: if `endTime < startTime`, add 1 day to end

## Schedulers

Two watchdog threads poll state files every 10s, start/stop the actual scheduler thread:

- **Club** (`SignScheduler`, 60s interval): polls `get_sign_in_tf()`, auto sign-in/back during activity window. Before window → sleep until start; after window → sleep 1h.
- **Run** (`RunScheduler`, 120s interval): checks weekday + time range, submits one fake run/day via `save_run_record_v2`.

State files (`.data/scheduler_club.json`, `.data/scheduler_run.json`) use `threading.Lock()`. Scheduler API calls do not handle token expiry.

## Frontend

`src/frontend/` — Streamlit 1.57.0, 5 pages: 首页/跑步/俱乐部/我的/关于. Login gate checks `ctx.user.studentId`. Sidebar via `st.session_state.page`. Custom CSS at `style.css`.

## Notes

- `.data/` (gitignored) — `.token`, `.user`, scheduler state files, `app.log`. Log truncated on every start.
- `AMAP_KEY` / `AMAP_SECURITY` optional — enables AMap tiles in folium + drawer at `http://127.0.0.1:8852/drawer.html`
- `java/` dir gitignored (decompiled APK reference)
- No test framework. `test.py` is ad-hoc interactive CLI.
