#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import platform
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

# tqdm==4.67.3 required


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")
os.environ["PYTHONIOENCODING"] = "utf-8"


def pause_and_exit(code=0):
    input("\n  按 Enter 键退出...")
    sys.exit(code)


SELF_DIR = Path(__file__).resolve().parent
os.chdir(str(SELF_DIR))

if getattr(sys, 'frozen', False):
    _INSTALLER_DIR = Path(sys.executable).resolve().parent
else:
    _INSTALLER_DIR = SELF_DIR
_TARGET_DIR = _INSTALLER_DIR.parent
VER_FILE = SELF_DIR / ".installed_ver"

USE_COLOR = platform.system() != "Windows"

DEFAULT_CONFIG = {
    "repo_url": "https://github.com/csy214-beep/PaceTrace.git",
    "branch": "main",
    "python_version": "3.11",
    "min_python_version": (3, 10),
    "project_dir": "PaceTrace",
}

CONFIG = dict(DEFAULT_CONFIG)

RAW_BASE = "https://gitee.com/{owner}/{repo}/raw/{branch}/installer/config.json"


def _parse_repo_url(url: str):
    parts = url.rstrip(".git").rstrip("/").split("/")
    return parts[-2], parts[-1]


def fetch_config():
    owner, repo_name = _parse_repo_url(CONFIG["repo_url"])
    branch = CONFIG["branch"]
    url = RAW_BASE.format(owner=owner, repo=repo_name, branch=branch)
    cprint(f"\n[配置] 从 GitHub 获取远程配置...", "cyan")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "PaceTrace-Installer"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            import json
            remote = json.loads(resp.read().decode("utf-8"))
            CONFIG.update(remote)
            cprint("  远程配置加载成功！", "green")
            return
    except Exception as e:
        cprint(f"  获取远程配置失败: {e}", "yellow")
        cprint("  使用本地默认配置", "yellow")


def cprint(msg: str, color: str = ""):
    codes = {"green": "32", "yellow": "33", "red": "31", "cyan": "36", "bold": "1"}
    if USE_COLOR and color:
        c = codes.get(color, "")
        print(f"\033[{c}m{msg}\033[0m")
    else:
        print(msg)


def shell(cmd, cwd=None, capture=False):
    cprint(f"  $ {' '.join(cmd)}", "cyan")
    kw = {"cwd": cwd}
    if capture:
        kw["capture_output"] = True
        kw["text"] = True
    try:
        return subprocess.run(cmd, **kw)
    except FileNotFoundError:
        cprint(f"  [!] 找不到命令: {cmd[0]}", "red")
        return None
    except Exception as e:
        cprint(f"  [!] 执行失败: {e}", "red")
        return None


def confirm(msg: str) -> bool:
    reply = input(f"  {msg} (Y/n): ").strip().lower()
    return reply in ("", "y", "yes")


def detect_python():
    for exe in ["python3", "python"]:
        r = shell([exe, "--version"], capture=True)
        if r and r.returncode == 0:
            raw = (r.stdout or r.stderr or "").strip()
            for word in raw.replace("Python ", "").split():
                parts = word.split(".")
                if len(parts) >= 2:
                    try:
                        ver = tuple(int(p) for p in parts[:3])
                        return exe, ver
                    except ValueError:
                        continue
    return None, None


def _have_git() -> bool:
    r = shell(["git", "--version"], capture=True)
    return r is not None and r.returncode == 0


def git_clone(url: str, path: str, branch: str) -> bool:
    cprint(f"\n[仓库] 正在克隆 {url} ({branch})，请稍等...", "cyan")
    r = shell(["git", "clone", "--branch", branch, "--depth", "1", url, path])
    if r and r.returncode == 0:
        cprint("  克隆完成！", "green")
        return True
    return False


def git_update(path: str, branch: str) -> bool:
    cprint(f"\n[仓库] 正在更新，请稍等...", "cyan")
    shell(["git", "fetch", "--tags"], cwd=path)
    shell(["git", "checkout", branch], cwd=path)
    r = shell(["git", "pull", "origin", branch], cwd=path)
    if r and r.returncode == 0:
        cprint("  更新完成！", "green")
        return True
    return False


def git_head(path: str) -> str:
    r = shell(["git", "rev-parse", "HEAD"], cwd=path, capture=True)
    if r and r.returncode == 0:
        return r.stdout.strip()
    return ""


def ensure_git():
    if _have_git():
        return True
    cprint("\n[Git] 未检测到 Git", "yellow")
    if not confirm("是否下载安装 Git?"):
        cprint("  已跳过，退出程序", "yellow")
        pause_and_exit(0)
    s = platform.system()
    if s == "Windows":
        url = "https://github.com/git-for-windows/git/releases/download/v2.49.0.windows.1/Git-2.49.0-64-bit.exe"
        dst = str(SELF_DIR / "Git-2.49.0-64-bit.exe")
        if download_file(url, dst):
            cprint("  正在安装 Git...", "yellow")
            subprocess.run([dst, "/VERYSILENT", "/NORESTART", "/NOCANCEL"])
            if _have_git():
                cprint("  Git 安装成功！", "green")
                return True
        for tool, cmd in [
            (
                "winget",
                ["winget", "install", "--id", "Git.Git", "-e", "--source", "winget"],
            ),
            ("choco", ["choco", "install", "git", "-y"]),
            ("scoop", ["scoop", "install", "git"]),
        ]:
            cprint(f"  尝试通过 {tool} 安装...", "yellow")
            r = shell(["where", tool], capture=True)
            if r and r.returncode == 0:
                shell(cmd)
                if _have_git():
                    cprint("  Git 安装成功！", "green")
                    return True
        cprint("  请手动安装 Git: https://git-scm.com/downloads", "red")
        pause_and_exit(1)
    elif s == "Darwin":
        url = "https://sourceforge.net/projects/git-osx-installer/files/git-2.49.0-intel-universal-mavericks.dmg"
        dst = str(SELF_DIR / "git.dmg")
        if download_file(url, dst):
            cprint("  正在安装 Git...", "yellow")
            subprocess.run(["sudo", "hdiutil", "attach", dst])
            subprocess.run(
                [
                    "sudo",
                    "installer",
                    "-pkg",
                    "/Volumes/Git/Installer.pkg",
                    "-target",
                    "/",
                ]
            )
            subprocess.run(["sudo", "hdiutil", "detach", "/Volumes/Git"])
            if _have_git():
                cprint("  Git 安装成功！", "green")
                return True
        for tool, cmd in [
            ("Homebrew", ["brew", "install", "git"]),
            ("MacPorts", ["port", "install", "git"]),
        ]:
            cprint(f"  尝试通过 {tool} 安装...", "yellow")
            r = shell(["which", tool.lower()], capture=True)
            if r and r.returncode == 0:
                shell(cmd)
                if _have_git():
                    cprint("  Git 安装成功！", "green")
                    return True
        cprint("  请手动安装 Git: https://git-scm.com/downloads", "red")
        pause_and_exit(1)
    else:
        url = "https://www.kernel.org/pub/software/scm/git/git-2.49.0.tar.xz"
        dst = str(SELF_DIR / "git.tar.xz")
        if download_file(url, dst):
            cprint("  已下载源码包到 installer 目录，可手动编译安装", "yellow")
        cprint("  尝试通过系统包管理器安装...", "yellow")
        dist = _detect_linux()
        pms = []
        if "ubuntu" in dist or "debian" in dist:
            pms = [("apt", ["sudo", "apt", "install", "-y", "git"])]
        elif "fedora" in dist:
            pms = [("dnf", ["sudo", "dnf", "install", "-y", "git"])]
        elif "centos" in dist or "rhel" in dist:
            pms = [("yum", ["sudo", "yum", "install", "-y", "git"])]
        elif "arch" in dist:
            pms = [("pacman", ["sudo", "pacman", "-S", "--noconfirm", "git"])]
        elif "opensuse" in dist or "suse" in dist:
            pms = [("zypper", ["sudo", "zypper", "install", "-y", "git"])]
        elif "alpine" in dist:
            pms = [("apk", ["sudo", "apk", "add", "git"])]
        else:
            pms = [
                ("apt", ["sudo", "apt", "install", "-y", "git"]),
                ("dnf", ["sudo", "dnf", "install", "-y", "git"]),
                ("pacman", ["sudo", "pacman", "-S", "--noconfirm", "git"]),
                ("zypper", ["sudo", "zypper", "install", "-y", "git"]),
                ("apk", ["sudo", "apk", "add", "git"]),
            ]
        for name, cmd in pms:
            r = shell(["which", name], capture=True)
            if r is None or r.returncode != 0:
                continue
            cprint(f"  尝试通过 {name} 安装...", "yellow")
            shell(cmd)
            if _have_git():
                cprint("  Git 安装成功！", "green")
                return True
        cprint("  请手动安装 Git: https://git-scm.com/downloads", "red")
        pause_and_exit(1)


def download_file(url: str, dst: str) -> bool:
    try:
        import requests
        from tqdm import tqdm

        cprint("  通过 requests + tqdm 下载...", "cyan")
        head = requests.head(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        total = int(head.headers.get("Content-Length", 0))
        r = requests.get(
            url, stream=True, timeout=120, headers={"User-Agent": "Mozilla/5.0"}
        )
        r.raise_for_status()
        desc = Path(dst).name
        with open(dst, "wb") as f, tqdm(
            desc=desc,
            total=total,
            unit="B",
            unit_scale=True,
            unit_divisor=1024,
            miniters=1,
            ncols=60,
        ) as bar:
            for chunk in r.iter_content(131072):
                f.write(chunk)
                bar.update(len(chunk))
        if Path(dst).exists() and Path(dst).stat().st_size > 0:
            return True
    except ImportError:
        pass
    except Exception as e:
        cprint(f"  第三方库下载失败: {e}", "yellow")

    s = platform.system()
    try:
        if s == "Windows":
            cprint("  通过 PowerShell 下载...", "cyan")
            r = subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-Command",
                    f"Invoke-WebRequest -Uri '{url}' -OutFile '{dst}' -UseBasicParsing",
                ],
                capture_output=True,
                text=True,
            )
            if (
                r.returncode == 0
                and Path(dst).exists()
                and Path(dst).stat().st_size > 0
            ):
                return True
            r = subprocess.run(["curl", "-fsSL", "-o", dst, url], capture_output=True)
            if (
                r.returncode == 0
                and Path(dst).exists()
                and Path(dst).stat().st_size > 0
            ):
                return True
        elif s == "Darwin":
            cprint("  通过 curl 下载...", "cyan")
            r = subprocess.run(["curl", "-fsSL", "-o", dst, url])
            if (
                r.returncode == 0
                and Path(dst).exists()
                and Path(dst).stat().st_size > 0
            ):
                return True
        else:
            if subprocess.run(["which", "wget"], capture_output=True).returncode == 0:
                cprint("  通过 wget 下载...", "cyan")
                r = subprocess.run(["wget", "-q", "--show-progress", "-O", dst, url])
                if (
                    r.returncode == 0
                    and Path(dst).exists()
                    and Path(dst).stat().st_size > 0
                ):
                    return True
            cprint("  通过 curl 下载...", "cyan")
            r = subprocess.run(["curl", "-fsSL", "-o", dst, url])
            if (
                r.returncode == 0
                and Path(dst).exists()
                and Path(dst).stat().st_size > 0
            ):
                return True
    except Exception:
        pass

    cprint("  尝试 Python urllib 下载...", "yellow")
    try:
        urllib.request.urlretrieve(url, dst)
        if Path(dst).exists() and Path(dst).stat().st_size > 0:
            return True
    except Exception:
        pass
    return False


def install_python():
    py_ver = CONFIG["python_version"]
    cprint(f"\n[Python] 未检测到 Python {py_ver}", "yellow")
    if not confirm(f"是否下载安装 Python {py_ver}?"):
        cprint("  已跳过，退出程序", "yellow")
        pause_and_exit(0)
    s = platform.system()
    if s == "Windows":
        urls = {
            "3.11": "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe",
            "3.12": "https://www.python.org/ftp/python/3.12.9/python-3.12.9-amd64.exe",
            "3.13": "https://www.python.org/ftp/python/3.13.3/python-3.13.3-amd64.exe",
        }
        url = urls.get(py_ver, urls["3.11"])
        dst = str(SELF_DIR / f"python-{py_ver}-amd64.exe")
        if download_file(url, dst):
            cprint("  正在运行安装程序，请稍等...", "yellow")
            r = subprocess.run([dst, "/quiet", "InstallAllUsers=1", "PrependPath=1"])
            if r.returncode == 0:
                cprint("  Python 安装完成！请关闭窗口后重新运行。", "green")
            else:
                cprint(f"  安装程序执行失败 (code={r.returncode})", "red")
                cprint("  请手动安装: https://www.python.org/downloads/", "red")
        else:
            cprint("  下载失败，请手动安装: https://www.python.org/downloads/", "red")
        pause_and_exit(0)
    if s == "Darwin":
        url = f"https://www.python.org/ftp/python/{py_ver}.9/python-{py_ver}.9-macos11.pkg"
        dst = str(SELF_DIR / f"python-{py_ver}-macos.pkg")
        if download_file(url, dst):
            cprint("  正在运行安装程序，请稍等...", "yellow")
            r = subprocess.run(["sudo", "installer", "-pkg", dst, "-target", "/"])
            if r.returncode == 0:
                cprint("  Python 安装完成！请重新运行。", "green")
            else:
                cprint(f"  安装失败 (code={r.returncode})", "red")
        else:
            cprint("  下载失败，请手动安装: https://www.python.org/downloads/", "red")
        pause_and_exit(0)
    if s == "Linux":
        url = f"https://www.python.org/ftp/python/{py_ver}.9/Python-{py_ver}.9.tar.xz"
        dst = str(SELF_DIR / f"Python-{py_ver}.9.tar.xz")
        if download_file(url, dst):
            cprint("  请手动解压并编译安装，或改用系统包管理器:", "yellow")
        cprint("  尝试通过系统包管理器安装...", "yellow")
        dist = _detect_linux()
        if "ubuntu" in dist or "debian" in dist:
            shell(["sudo", "apt", "update"])
            shell(
                [
                    "sudo",
                    "apt",
                    "install",
                    "-y",
                    "python3",
                    "python3-venv",
                    "python3-pip",
                ]
            )
        elif "fedora" in dist or "centos" in dist:
            shell(["sudo", "dnf", "install", "-y", "python3", "python3-pip"])
        elif "arch" in dist:
            shell(["sudo", "pacman", "-S", "--noconfirm", "python", "python-pip"])
        else:
            cprint("  请手动安装 Python: https://www.python.org/downloads/", "red")
            pause_and_exit(1)
        cprint("  Python 安装完成！请重新运行。", "green")
        pause_and_exit(0)
    cprint(f"  不支持的操作系统: {s}", "red")
    pause_and_exit(1)


def _detect_linux():
    try:
        with open("/etc/os-release", encoding="utf-8") as f:
            for line in f:
                if line.startswith("ID="):
                    return line.strip().split("=", 1)[1].strip('"').lower()
    except Exception:
        pass
    return ""


def find_project():
    name = CONFIG["project_dir"]
    candidate = _TARGET_DIR / name

    if candidate.exists() and (candidate / "run.py").exists():
        cprint(f"\n[仓库] 发现已有项目: {candidate}", "cyan")
        return str(candidate), True

    return str(candidate), False


def update_project(project_dir):
    url = CONFIG["repo_url"]
    branch = CONFIG["branch"]
    target = Path(project_dir)

    if (target / ".git").exists():
        if not git_update(str(target), branch):
            cprint("  更新失败，请检查网络或分支名", "red")
            pause_and_exit(1)
    else:
        if not git_clone(url, str(target), branch):
            cprint("  克隆失败，请检查仓库地址和网络", "red")
            pause_and_exit(1)


def setup_venv(project_dir):
    s = platform.system()
    venv_path = Path(project_dir) / ".venv"
    bin_dir = "Scripts" if s == "Windows" else "bin"
    pip_path = str(venv_path / bin_dir / "pip")
    python_path = str(venv_path / bin_dir / "python")

    if venv_path.exists():
        cprint(f"\n[虚拟环境] .venv 已存在，跳过创建", "cyan")
    else:
        cprint(f"\n[虚拟环境] 正在创建 .venv，请稍等...", "cyan")
        r = shell([sys.executable, "-m", "venv", str(venv_path)])
        if r and r.returncode == 0:
            cprint("  虚拟环境创建成功！", "green")
        else:
            cprint("  虚拟环境创建失败！", "red")
            pause_and_exit(1)

    cprint("\n[依赖] 正在升级 pip，请稍等...", "cyan")
    shell([python_path, "-m", "pip", "install", "--upgrade", "pip"])

    cprint("[依赖] 正在安装项目依赖，请稍等...", "cyan")
    req = Path(project_dir) / "requirements.txt"
    if req.exists():
        r = shell([pip_path, "install", "-r", str(req)])
        if r and r.returncode == 0:
            cprint("  依赖安装完成！", "green")
        else:
            cprint("  部分依赖安装失败，请检查上方日志", "red")
            pause_and_exit(1)
    else:
        cprint("  未找到 requirements.txt，跳过", "yellow")

    return python_path


def ensure_env_file(project_dir):
    env_file = Path(project_dir) / ".env"
    env_example = Path(project_dir) / ".env.example"

    if env_file.exists():
        cprint(f"\n[配置] .env 已存在，跳过", "cyan")
        return

    if env_example.exists():
        cprint(f"\n[配置] 正在从 .env.example 创建 .env，请稍等...", "yellow")
        shutil.copy2(str(env_example), str(env_file))
        cprint(f"  已创建！请编辑 .env 填入你的密钥", "yellow")
    else:
        cprint(f"\n[配置] 未找到 .env.example，跳过", "yellow")


def track_version(project_dir):
    cur = git_head(project_dir)
    if cur:
        old = VER_FILE.read_text(encoding="utf-8").strip() if VER_FILE.exists() else ""
        VER_FILE.write_text(cur, encoding="utf-8")
        if old and old != cur:
            cprint(f"\n[版本] 已更新: {old[:12]} -> {cur[:12]}", "green")
        else:
            cprint(f"\n[版本] 当前: {cur[:12]}", "cyan")


def launch(project_dir, python_path):
    cprint("\n" + "=" * 50, "bold")
    cprint("  正在启动 PaceTrace，请稍等...", "bold")
    cprint("=" * 50, "bold")
    cprint("  浏览器打开 http://localhost:8501", "cyan")
    cprint("  轨迹画板: http://localhost:8852/drawer.html", "cyan")
    cprint("  按 Ctrl+C 停止", "yellow")
    cprint("=" * 50 + "\n", "bold")
    os.chdir(project_dir)
    shell([python_path, "run.py"])


def main():
    print()
    cprint("=" * 50, "bold")
    cprint("  PaceTrace 行迹 安装/更新工具", "bold")
    cprint("=" * 50, "bold")
    fetch_config()
    cprint(f"  仓库: {CONFIG['repo_url']} ({CONFIG['branch']})", "cyan")
    cprint(f"  系统: {platform.system()} {platform.release()}", "cyan")

    # ── 步骤 1: 环境检查 ──────────────────────────────
    cprint("\n>>> [步骤 1/5] 检查 Python / Git 环境", "bold")
    min_ver = tuple(CONFIG["min_python_version"])
    exe, ver = detect_python()
    if exe:
        ver_str = ".".join(str(v) for v in ver)
        cprint(f"  [Python] {exe} {ver_str}", "green")
        if ver < min_ver:
            need = ".".join(str(v) for v in min_ver)
            cprint(f"  版本过低 ({ver_str})，需要 >= {need}", "red")
            install_python()
    else:
        install_python()
    ensure_git()

    # ── 步骤 2: 克隆/更新 ─────────────────────────────
    project_dir, exists = find_project()
    cprint(f"\n>>> [步骤 2/5] 克隆 / 更新项目代码", "bold")
    if not exists:
        if not confirm("项目不存在，是否克隆?"):
            cprint("  已退出", "yellow")
            pause_and_exit(0)
        update_project(project_dir)
    elif confirm("是否更新项目代码?"):
        update_project(project_dir)
    else:
        cprint("  跳过", "cyan")

    # ── 步骤 3: 虚拟环境 ──────────────────────────────
    cprint(f"\n>>> [步骤 3/5] 配置虚拟环境 + 安装依赖", "bold")
    python_path = None
    if confirm("是否配置虚拟环境?"):
        python_path = setup_venv(project_dir)
        track_version(project_dir)
    else:
        cprint("  跳过", "cyan")

    # ── 步骤 4: .env 配置 ─────────────────────────────
    cprint(f"\n>>> [步骤 4/5] 配置 .env 文件", "bold")
    if confirm("是否配置 .env 文件?"):
        ensure_env_file(project_dir)
    else:
        cprint("  跳过", "cyan")

    # ── 步骤 5: 启动 ──────────────────────────────────
    cprint(f"\n>>> [步骤 5/5] 启动项目", "bold")
    if confirm("是否启动项目?"):
        if not python_path:
            s = platform.system()
            bin_dir = "Scripts" if s == "Windows" else "bin"
            python_path = str(Path(project_dir) / ".venv" / bin_dir / "python")
            if not Path(python_path).exists():
                cprint("  [!] 虚拟环境未配置，无法启动", "red")
                cprint("  请重新运行并选择步骤 3", "yellow")
                pause_and_exit(1)
        launch(project_dir, python_path)
    else:
        cprint("  手动运行:", "yellow")
        sep = "\\" if platform.system() == "Windows" else "/"
        cprint(f"  cd {project_dir} && .venv{sep}python run.py", "cyan")

    cprint("\n  完成！", "green")
    input("\n  按 Enter 键退出...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        cprint("\n  已取消", "yellow")
        input("\n  按 Enter 键退出...")
        sys.exit(0)
    except Exception as e:
        cprint(f"\n  [!] 未捕获异常: {e}", "red")
        input("\n  按 Enter 键退出...")
        sys.exit(1)
