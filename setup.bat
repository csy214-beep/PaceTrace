@echo off
chcp 65001 >nul
echo === 行迹 - 环境初始化 ===
echo.

if not exist ".venv\" (
    echo [1/2] 创建虚拟环境...
    python -m venv .venv
) else (
    echo [1/2] 虚拟环境已存在，跳过
)

echo [2/2] 安装依赖...
call .venv\Scripts\activate.bat
pip install -r requirements.txt
echo.
echo 初始化完成。运行 run.bat 启动程序。
pause
