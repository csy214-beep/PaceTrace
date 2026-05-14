# PaceTrace — Agent Guide

## Quick start

```bash
python -m venv .venv && .venv\Scripts\activate && pip install -r requirements.txt
python run.py  # launches Streamlit UI + tray + scheduler threads
```

## Entry point

`run.py` — starts 4 daemon threads (static drawer server :8852, system tray, club scheduler, run scheduler), then launches the Streamlit UI via `streamlit.web.cli`.

## Project layout

```
run.py              # launcher
src/
  api/              # API client — custom MD5-based signature
  frontend/         # Streamlit pages
  scheduler/        # background threads for auto sign-in & run
  maps/             # route JSON files
  tray/             # system tray icon
```

## API client quirks

`src/api/client.py` — every request is signed via `_build_sign()`:
1. Sorts query params alphabetically, flattens `k=v`
2. Concatenates: `k1v1k2v2...` + `APPKEY` + `APPSECRET` + (body JSON if POST)
3. MD5 of above, uppercase → `sign` header

Required env vars: `APPKEY`, `APPSECRET`, `BASE_URL`, `UA`. Copy `.env.example` → `.env`.

## Club sign-in/back flow

1. `club.get_sign_in_tf()` returns venue lat/lng + activity window + `signStatus`
2. `scheduler/club.py` polls every 60s; when inside activity window, checks `signStatus`:
   - `"0"` → POST `signInOrSignBack` with `signType: "1"` (sign in)
   - `"1"` → POST `signInOrSignBack` with `signType: "2"` (sign back)
3. Coordinates offset 100m from venue coords (`_random_point`)
4. POST body matches Java `SignBody`: `activityId`, `latitude`, `longitude`, `signType`, `studentId`

## Run submission

Track point format (`lng-lat-timestamp-accuracy`):
```json
["104.3-30.6-1683988800000-8"]
```
- 4th field = GPS accuracy in meters (5–10)
- `year_semester` MUST be fetched from `get_run_standard().semesterYear` — never hardcode (was hardcoded as `"20261"`, already fixed)
- Schedulers and frontend both call `save_run_record_v2` (the `/new` endpoint)

## Maps

`src/maps/*.json` format:
```json
{"mapId":"1","mapName":"操场","mapData":["lng1,lat1","lng2,lat2",...]}
```
Coordinates in GCJ-02 (高德坐标系).

## Schedulers

Two independent background threads (controlled via `.data/scheduler_club.json` and `.data/scheduler_run.json`):
- Club: polls `get_sign_in_tf()` every 60s, auto sign-in/back
- Run: checks weekday + time range schedule, submits fake run once per day

## Data storage

`.data/` (gitignored):
- `.token` — cached auth token
- `.user` — serialized user info
- `scheduler_club.json`, `scheduler_run.json` — scheduler states
- `app.log` — operation log

## Notable gotchas

- `os.system` calls fail on Windows with spaces in Python path → use `streamlit.web.cli` directly (done in `run.py`)
- Year semester tie: `save_run_record` v1 is unused; `save_run_record_v2` is the active endpoint
- No test framework or CI tests — `test.py` exists but is ad-hoc
- Java reference code in `java/` dir is gitignored (decompiled Android APK)
