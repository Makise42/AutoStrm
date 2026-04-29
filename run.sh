#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"
PYTHON_BIN="${PYTHON_BIN:-python3}"

while true; do
  echo "================ AutoStrm ================"
  echo "1. 手动运行 Openlist2Strm"
  echo "2. 手动运行 Ani2Openlist"
  echo "3. 拉取所有Ani Open番剧"
  echo "4. 退出脚本"
  echo "==========================================="
  read -r -p "请选择: " choice

  case "$choice" in
    1)
      "$PYTHON_BIN" -m app.main o2s
      ;;
    2)
      "$PYTHON_BIN" -m app.main a2o
      ;;
    3)
      "$PYTHON_BIN" -m app.main a2o-all
      ;;
    4)
      exit 0
      ;;
    *)
      echo "无效选项，请重新选择。"
      ;;
  esac
done
