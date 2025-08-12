#!/bin/bash
echo "启动 Weekly Tracker for macOS..."
cd "$(dirname "$0")"
python3 wp_gui_final.py &
echo "程序已在后台启动，请查看菜单栏图标"
