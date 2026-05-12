#!/usr/bin/env python
"""启动 行迹 PaceTrace 前端"""
import os

if __name__ == "__main__":
    os.system(f"streamlit run {os.path.join(os.path.dirname(__file__), 'frontend', 'app.py')}")
