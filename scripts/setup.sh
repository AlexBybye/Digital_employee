#!/bin/bash

BASE_DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo "========================================"
echo "   Starting services in new windows..."
echo "========================================"

# 1. 新窗口启动后端（使用 backend/.venv，离线加载本地模型）
echo "[1/2] Launching backend..."
osascript -e "tell application \"Terminal\" to do script \"cd '$BASE_DIR/backend' && HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 .venv/bin/uvicorn main:app --port 8001\""

sleep 3

# 2. 新窗口启动前端（Vue + Vite dev server）
echo "[2/2] Launching frontend (Vue + Vite)..."
osascript -e "tell application \"Terminal\" to do script \"cd '$BASE_DIR/frontend-vue' && (test -d node_modules || npm install) && npm run dev\""

echo ""
echo .
echo ========================================
echo   Services are running!
echo ========================================
echo .
echo Frontend: http://127.0.0.1:5173/
echo Backend:  http://127.0.0.1:8001
echo Docs:     http://127.0.0.1:8001/docs
echo .
echo Close this window when done.
echo .
