@echo off
setlocal enabledelayedexpansion

:: ====================== 配置 ======================
set "MIRROR=https://pypi.tuna.tsinghua.edu.cn/simple"
set "PROJ_DIR=PaceTrace"
set "MIN_MAJOR=3"
set "MIN_MINOR=10"

:: 切换到脚本所在目录，并记录绝对路径供后续使用
cd /d "%~dp0"
set "SCRIPT_DIR=%~dp0"

:: ====================== 主菜单 ======================
:menu
cls
echo ==============================================
echo   PaceTrace 行迹  安装 / 启动工具
echo   版本: 20260514.3
echo ==============================================
echo   1  完整安装 / 更新
echo   2  直接启动（跳过安装）
echo   3  添加到开机启动
echo   4  退出
echo.
set /p "opt=请选择 (1/2/3/4): "
if "%opt%"=="1" goto install
if "%opt%"=="2" goto launch
if "%opt%"=="3" goto add_startup
if "%opt%"=="4" goto end
echo 请输入 1、2、3 或 4
pause
goto menu

:: ====================== 查找可用 Python ===============
:: 修复核心问题：用 where 取完整路径，避免被 Microsoft Store stub 劫持
:find_python
set "PY_EXE="
set "PY_VER="
for %%c in (py python3 python) do (
    if "!PY_EXE!"=="" (
        for /f "tokens=* usebackq" %%p in (`where %%c 2^>nul`) do (
            if "!PY_EXE!"=="" (
                :: 用完整路径执行，彻底跳过 Store stub
                for /f "tokens=2" %%v in ('"%%p" --version 2^>^&1') do set "ver=%%v"
                for /f "tokens=1,2 delims=." %%a in ("!ver!") do (
                    if %%a equ %MIN_MAJOR% if %%b geq %MIN_MINOR% (
                        set "PY_EXE=%%p"
                        set "PY_VER=%%a.%%b"
                        goto :eof
                    )
                    if %%a gtr %MIN_MAJOR% (
                        set "PY_EXE=%%p"
                        set "PY_VER=%%a.%%b"
                        goto :eof
                    )
                )
            )
        )
    )
)
goto :eof

:: ====================== 完整安装 / 更新 ===============
:install
echo.
echo [1/3] 检查 Python 环境
call :find_python
if "%PY_EXE%"=="" (
    echo   未找到 Python ^>= 3.10，请先安装：
    echo   https://www.python.org/downloads/
    echo   安装时请勾选 "Add Python to PATH"
    pause
    exit /b 1
)
echo   Python %PY_VER% √  路径: %PY_EXE%

echo.
echo [2/3] 克隆 / 更新项目代码
where git >nul 2>nul
if errorlevel 1 (
    echo   未找到 Git，请先安装：https://git-scm.com/downloads
    pause
    exit /b 1
)

:: 选择仓库源
echo 请选择仓库源:
echo   1. GitHub  (github.com/igugyj/pacetrace)
echo   2. Gitee   (gitee.com/pfolg/pacetrace) [推荐]
set /p "repo_opt=请输入 1 或 2: "
if "%repo_opt%"=="1" set "REPO_URL=https://github.com/igugyj/pacetrace.git"
if "%repo_opt%"=="2" set "REPO_URL=https://gitee.com/pfolg/pacetrace.git"
if "%REPO_URL%"=="" (
    echo   无效选择，默认使用 GitHub
    set "REPO_URL=https://github.com/igugyj/pacetrace.git"
)

:: 询问是否同步代码
set /p "do_sync=克隆/更新项目代码？ (Y/n) "
if /i "%do_sync%"=="" set do_sync=Y
if /i "%do_sync%"=="Y" (
    if exist "%PROJ_DIR%\.git" (
        echo   更新代码...
        pushd "%PROJ_DIR%"
        git pull origin main
        popd
    ) else (
        echo   克隆仓库...
        git clone --branch main --depth 1 "%REPO_URL%" "%PROJ_DIR%"
    )
    if not exist "%PROJ_DIR%\run.py" (
        echo   代码获取失败，请检查网络或仓库地址
        pause
        exit /b 1
    )
    echo   代码同步完成 √
) else (
    echo   跳过
)

echo.
echo [3/4] 初始化配置文件
if exist "%PROJ_DIR%\.env.example" (
    if not exist "%PROJ_DIR%\.env" (
        copy "%PROJ_DIR%\.env.example" "%PROJ_DIR%\.env" >nul
        echo   .env.example -^> .env  √  请按需编辑 %PROJ_DIR%\.env
    ) else (
        echo   .env 已存在，跳过（不覆盖现有配置）
    )
) else (
    echo   未找到 .env.example，跳过
)

echo.
echo [4/4] 配置虚拟环境 + 安装依赖
set /p "do_venv=配置虚拟环境并安装依赖？ (Y/n) "
if /i "%do_venv%"=="" set do_venv=Y
if /i "%do_venv%" neq "Y" (
    echo   跳过
    goto ask_launch
)

if not exist "%PROJ_DIR%\.venv" (
    echo   创建虚拟环境...
    "%PY_EXE%" -m venv "%PROJ_DIR%\.venv"
    if errorlevel 1 (
        echo   虚拟环境创建失败
        echo   Python 路径: %PY_EXE%
        echo   请确认该 Python 安装完整（含标准库）
        pause
        exit /b 1
    )
) else (
    echo   虚拟环境已存在，跳过创建
)

:: 二次确认 venv 里的 python.exe 真实存在
if not exist "%PROJ_DIR%\.venv\Scripts\python.exe" (
    echo   虚拟环境不完整，尝试重建...
    rmdir /s /q "%PROJ_DIR%\.venv"
    "%PY_EXE%" -m venv "%PROJ_DIR%\.venv"
    if not exist "%PROJ_DIR%\.venv\Scripts\python.exe" (
        echo   虚拟环境重建失败，请检查 Python 安装
        pause
        exit /b 1
    )
)
echo   虚拟环境已就绪 √

echo   升级 pip...
"%PROJ_DIR%\.venv\Scripts\python.exe" -m pip install --upgrade pip -i %MIRROR% --quiet

if exist "%PROJ_DIR%\requirements.txt" (
    echo   安装依赖...
    "%PROJ_DIR%\.venv\Scripts\python.exe" -m pip install -r "%PROJ_DIR%\requirements.txt" -i %MIRROR%
    if errorlevel 1 (
        echo   依赖安装失败，请检查日志
        pause
        exit /b 1
    )
    echo   依赖安装完成 √
) else (
    echo   未找到 requirements.txt，跳过依赖安装
)

:ask_launch
set /p "start_now=安装完成！现在启动 PaceTrace？ (Y/n) "
if /i "%start_now%"=="" set start_now=Y
if /i "%start_now%"=="Y" goto launch
echo   手动启动：cd %PROJ_DIR% ^&^& .venv\Scripts\python run.py
pause
exit /b 0

:: ====================== 直接启动 ======================
:launch
:: 在 cd 之前用绝对路径锁定 venv python
:: （cd 之后相对路径失效，是 ModuleNotFoundError 的根本原因）
set "VENV_PYTHON=%SCRIPT_DIR%%PROJ_DIR%\.venv\Scripts\python.exe"
if not exist "%VENV_PYTHON%" (
    echo   虚拟环境不存在，请先完整安装（选项 1）
    pause
    exit /b 1
)

echo.
echo ==============================================
echo   PaceTrace 启动中，请稍候...
echo   主界面:   http://localhost:8501
echo   轨迹画板: http://localhost:8852/drawer.html
echo   程序运行中，此界面不可关闭！
echo   Ctrl+C 停止
echo ==============================================
echo.

set "VIRTUAL_ENV=%SCRIPT_DIR%%PROJ_DIR%\.venv"
set "PYTHONHOME="

cd "%SCRIPT_DIR%%PROJ_DIR%"
"%VENV_PYTHON%" run.py
echo.
echo   程序已退出（返回码 %errorlevel%）
pause
exit /b %errorlevel%

:: ====================== 添加到开机启动 ==================
:add_startup
echo.
set "STARTUP_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "SHORTCUT=%STARTUP_DIR%\PaceTrace.lnk"
if exist "%SHORTCUT%" (
    echo   快捷方式已存在，准备重新创建
    set /p "del_old=   是否删除原快捷方式？ (Y/n) "
    if /i "!del_old!"=="" set del_old=Y
    if /i "!del_old!"=="Y" del /f /q "%SHORTCUT%" >nul 2>nul
)
if not exist "%SHORTCUT%" (
    powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%SHORTCUT%'); $s.TargetPath = '%~f0'; $s.WorkingDirectory = '%SCRIPT_DIR%%PROJ_DIR%'; $s.Description = 'PaceTrace - 自动运行'; $s.Save()" >nul 2>nul
    if exist "%SHORTCUT%" (
        echo   开机启动添加成功  位置: %SHORTCUT%
    ) else (
        echo   添加失败，请手动将 run.bat 复制到开始菜单启动文件夹
    )
) else (
    echo   保留原快捷方式，未做更改
)
echo.
pause
goto menu

:: ====================== 退出 ==========================
:end
exit /b 0