#!/usr/bin/env bash
set -e
echo "=== 行迹 - 环境初始化 ==="
echo ""

if [ ! -d ".venv" ]; then
    echo "[1/2] 创建虚拟环境..."
    python3 -m venv .venv
else
    echo "[1/2] 虚拟环境已存在，跳过"
fi

echo "[2/2] 安装依赖..."
source .venv/bin/activate
pip install -r requirements.txt
echo ""
echo "初始化完成。运行 bash run.sh 启动程序。"
