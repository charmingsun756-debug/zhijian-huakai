#!/bin/bash
# 指尖花开 - 双击启动（启动本地服务并自动打开浏览器）
cd "$(dirname "$0")"

if nc -z 127.0.0.1 8123 2>/dev/null; then
  echo "✿ 服务已在运行，直接打开页面…"
else
  python3 server.py &
  sleep 1
fi

open "http://127.0.0.1:8123/index.html"

echo ""
echo "✿ 指尖花开 已启动！浏览器页面已自动打开。"
echo "   · 请保持本窗口开着（最小化即可），关闭窗口即全部退出"
echo "   · 若浏览器提示使用摄像头，请点「允许」"

wait
