@echo off
chcp 65001 >nul
echo === 行迹 - 启动 ===
call .venv\Scripts\activate.bat
python run.py
pause
