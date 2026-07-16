# PaceTrace Launcher

Windows setup tool for PaceTrace — installs dependencies, manages the project, and launches the app.

## Requirements

- **CMake** >= 3.20
- **MinGW-w64 GCC** (tested with 14.x)
- On Windows 10/11 only.

## Build

```bash
cmake -B build -G "MinGW Makefiles" -DCMAKE_MAKE_PROGRAM=*/gcc/bin/make.exe launcher/
cmake --build build
```

Output: `build/launcher.exe` (single file, statically linked, zero external DLLs).

## Usage

Run `launcher.exe` from anywhere. It operates on a `PaceTrace\` subdirectory created next to itself.

### Menu

| Option | What it does |
|--------|-------------|
| **1  Full Install / Update** | Checks for `uv` (auto-installs if missing) and `git` → picks a repo source + branch → clones or pulls → copies `.env.example` → `uv sync` → optionally launches |
| **2  Launch** | Runs `uv run python run.py` in the project directory |
| **3  Add to Startup** | Creates a `.lnk` shortcut in the Windows Startup folder |
| **4  Uninstall** | Deletes the project directory |
| **5  Exit** | |

### Repo sources

Three options during install: GitHub, Gitee (default), or a custom URL. Branch defaults to `main`.
