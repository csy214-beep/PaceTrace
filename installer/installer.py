#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PaceTrace 安装 / 启动工具"""

import os, platform, shutil, subprocess, sys
from pathlib import Path

# ── 编码 ──────────────────────────────────────────────────
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
os.environ["PYTHONIOENCODING"] = "utf-8"

# ── 颜色输出 ───────────────────────────────────────────────
_WIN = platform.system() == "Windows"
_CODES = {"g": "32", "y": "33", "r": "31", "c": "36", "b": "1"}


def c(msg, k=""):
    code = _CODES.get(k)
    print(f"\033[{code}m{msg}\033[0m" if (not _WIN and code) else msg)


def ask(msg):
    return input(f"\n  {msg} (Y/n) ").strip().lower() in ("", "y", "yes")


def bye(code=0):
    input("\n  按 Enter 退出...")
    sys.exit(code)


# ── 路径 ──────────────────────────────────────────────────
ROOT = (
    Path(sys.executable if getattr(sys, "frozen", False) else __file__).resolve().parent
)
os.chdir(ROOT)

CONFIG = {
    "repo_url": "https://gitee.com/Pfolg/PaceTrace.git",
    "branch": "main",
    "min_ver": (3, 10),
    "proj_dir": "PaceTrace",
}
MIRROR = "https://pypi.tuna.tsinghua.edu.cn/simple"


def proj_path() -> Path:
    return ROOT / CONFIG["proj_dir"]


def venv_python() -> Path:
    name = "python.exe" if _WIN else "python"
    return proj_path() / ".venv" / ("Scripts" if _WIN else "bin") / name


# ── 命令执行 ───────────────────────────────────────────────
def run(cmd, cwd=None, env=None, capture=False):
    c(f"  $ {' '.join(str(x) for x in cmd)}", "c")
    try:
        return subprocess.run(
            cmd, cwd=cwd, env=env, capture_output=capture, text=capture
        )
    except FileNotFoundError:
        c(f"  找不到命令: {cmd[0]}", "r")
    except Exception as e:
        c(f"  执行失败: {e}", "r")


# ── 环境检测 ───────────────────────────────────────────────
def find_python():
    """返回满足最低版本要求的 Python 可执行文件名，否则返回 None"""
    for exe in ("python3", "python"):
        try:
            r = subprocess.run([exe, "--version"], capture_output=True, text=True)
            ver_str = (r.stdout or r.stderr).strip().split()[-1]
            ver = tuple(int(x) for x in ver_str.split(".")[:2])
            if ver >= CONFIG["min_ver"]:
                return exe, ver
        except Exception:
            continue
    return None, None


# ── Git 操作 ───────────────────────────────────────────────
def git_sync(proj: Path) -> bool:
    url, branch = CONFIG["repo_url"], CONFIG["branch"]
    if (proj / ".git").exists():
        c("  更新代码...", "c")
        run(["git", "pull", "origin", branch], cwd=proj)
    else:
        c("  克隆仓库...", "c")
        run(["git", "clone", "--branch", branch, "--depth", "1", url, str(proj)])
    return (proj / "run.py").exists()


# ── 虚拟环境 ───────────────────────────────────────────────
def setup_venv(py_exe: str, proj: Path) -> Path:
    venv = proj / ".venv"
    py = venv / ("Scripts" if _WIN else "bin") / ("python.exe" if _WIN else "python")

    if not venv.exists():
        c("  创建虚拟环境...", "c")
        r = run([py_exe, "-m", "venv", str(venv)])
        if not r or r.returncode != 0:
            c("  虚拟环境创建失败", "r")
            bye(1)
        c("  虚拟环境已就绪", "g")
    else:
        c("  虚拟环境已存在，跳过创建", "c")

    run([str(py), "-m", "pip", "install", "--upgrade", "pip", "-i", MIRROR])

    req = proj / "requirements.txt"
    if req.exists():
        r = run([str(py), "-m", "pip", "install", "-r", str(req), "-i", MIRROR])
        if not r or r.returncode != 0:
            c("  依赖安装失败，请检查日志", "r")
            bye(1)
        c("  依赖安装完成", "g")
    else:
        c("  未找到 requirements.txt，跳过依赖安装", "y")

    return py


# ── 启动 ──────────────────────────────────────────────────
def launch():
    py = venv_python()
    proj = proj_path()

    if not py.exists():
        c("  虚拟环境不存在，请先完整安装", "r")
        bye(1)

    c("\n" + "─" * 46, "b")
    c("  PaceTrace 启动中，请稍候...", "b")
    c("  主界面:   http://localhost:8501", "c")
    c("  轨迹画板: http://localhost:8852/drawer.html", "c")
    c("  Ctrl+C 停止", "y")
    c("─" * 46 + "\n", "b")

    # ✅ 关键：将 venv 的 bin 目录注入 PATH
    # 这样 run.py 内部启动的子进程（如 streamlit）也能找到正确路径
    env = os.environ.copy()
    bin_dir = str(py.parent)
    env["PATH"] = bin_dir + os.pathsep + env.get("PATH", "")
    env["VIRTUAL_ENV"] = str(py.parent.parent)
    env.pop("PYTHONHOME", None)  # 避免干扰 venv

    os.chdir(proj)
    r = subprocess.run([str(py), "run.py"], env=env)
    c(f"\n  程序已退出（返回码 {r.returncode}）", "g" if r.returncode == 0 else "r")
    bye(r.returncode)


# ── 完整安装 ───────────────────────────────────────────────
def install():
    proj = proj_path()

    # 1. Python
    c("\n[1/3] 检查 Python 环境", "b")
    py_exe, ver = find_python()
    if not py_exe:
        min_s = ".".join(map(str, CONFIG["min_ver"]))
        c(f"  未找到 Python >= {min_s}，请先安装：", "r")
        c("  https://www.python.org/downloads/", "c")
        bye(1)
    c(f"  Python {'.'.join(map(str, ver))} ✓", "g")

    # 2. 代码同步
    c("\n[2/3] 克隆 / 更新项目代码", "b")
    if not shutil.which("git"):
        c("  未找到 Git，请先安装：https://git-scm.com/downloads", "r")
        bye(1)
    if ask("克隆 / 更新项目代码？"):
        if not git_sync(proj):
            c("  代码获取失败，请检查网络或仓库地址", "r")
            bye(1)
        c("  代码同步完成 ✓", "g")
    else:
        c("  跳过", "y")

    # 3. 虚拟环境 + 依赖
    c("\n[3/3] 配置虚拟环境 + 安装依赖", "b")
    if ask("配置虚拟环境并安装依赖？"):
        setup_venv(py_exe, proj)
    else:
        c("  跳过", "y")

    # 启动确认
    if ask("安装完成！现在启动 PaceTrace？"):
        launch()
    else:
        sep = "\\" if _WIN else "/"
        c(f"  手动启动：cd {proj} && .venv{sep}bin{sep}python run.py", "c")
        bye(0)


# ── 入口 ──────────────────────────────────────────────────
def main():
    # 支持 --start / -s 直接启动
    if any(a in sys.argv for a in ("--start", "-s")):
        launch()

    c("\n" + "═" * 46, "b")
    c("  PaceTrace 行迹  安装 / 启动工具", "b")
    c("═" * 46, "b")
    c("  1  完整安装 / 更新", "c")
    c("  2  直接启动（跳过安装）", "c")
    c("  3  退出", "c")

    while True:
        ch = input("\n  请选择 (1/2/3): ").strip()
        if ch == "1":
            install()
            break
        if ch == "2":
            launch()
            break
        if ch == "3":
            bye()
            break
        c("  请输入 1、2 或 3", "y")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        c("\n  已取消", "y")
        bye(0)
    except Exception as e:
        c(f"\n  错误: {e}", "r")
        bye(1)
