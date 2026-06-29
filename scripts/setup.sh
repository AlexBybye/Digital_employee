@echo off
:: 设置字符集为 UTF-8，防止中文乱码
chcp 65001 >nul

:: 获取当前脚本所在目录的上一级目录（相当于 BASE_DIR）
cd /d "%~dp0.."
set "BASE_DIR=%cd%"

echo ========================================
echo   Starting services in new windows...
echo ========================================

:: 1. 新窗口启动后端（使用 backend\.venv，离线加载本地模型）
echo [1/2] Launching backend...
:: 设置环境变量并启动 uvicorn
start "Backend Service" cmd /k "cd /d "%BASE_DIR%\backend" && set HF_HUB_OFFLINE=1 && set TRANSFORMERS_OFFLINE=1 && .venv\Scripts\uvicorn main:app --port 8001"

:: 等待 3 秒
timeout /t 3 /nobreak >nul

:: 2. 新窗口启动前端（Vue + Vite dev server）
echo [2/2] Launching frontend (Vue + Vite)...
:: 检查 node_modules 是否存在，不存在则执行 npm install，然后启动项目
start "Frontend Service" cmd /k "cd /d "%BASE_DIR%\frontend-vue" && (if not exist node_modules npm install) && npm run dev"

echo.
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
pause