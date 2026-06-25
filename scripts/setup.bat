@echo off
:: 设置字符集为 UTF-8，防止中文乱码
chcp 65001 >nul

:: 获取当前脚本所在目录的上一级目录（相当于 BASE_DIR）
cd /d "%~dp0.."
set "BASE_DIR=%cd%"

echo ========================================
echo   Initializing and Starting Services...
echo ========================================

:: 1. 检查并准备后端环境
echo [1/3] Checking backend virtual environment...
cd /d "%BASE_DIR%\backend"

:: 如果 .venv 文件夹不存在，则自动创建并安装依赖
if not exist ".venv" (
    echo [! ] .venv not found. Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Python is not installed or not in PATH. Backend setup failed.
        goto :END
    )
    echo [* ] Virtual environment created. Installing requirements...
    call .venv\Scripts\activate
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Failed to install backend dependencies.
        goto :END
    )
    echo [* ] Backend dependencies installed successfully!
) else (
    echo [* ] Backend virtual environment already exists.
)

:: 返回根目录
cd /d "%BASE_DIR%"
timeout /t 1 /nobreak >nul

:: 2. 新窗口启动后端（离线加载本地模型）
echo [2/3] Launching backend...
start "Backend Service" cmd /k "cd /d "%BASE_DIR%\backend" && set HF_HUB_OFFLINE=1 && set TRANSFORMERS_OFFLINE=1 && "%BASE_DIR%\backend\.venv\Scripts\uvicorn" main:app --port 8001"

:: 等待 3 秒确保后端服务初始化
timeout /t 3 /nobreak >nul

:: 3. 新窗口启动前端（Vue + Vite dev server）
echo [3/3] Launching frontend (Vue + Vite)...
start "Frontend Service" cmd /k "cd /d "%BASE_DIR%\frontend-vue" && (if not exist node_modules npm install) && npm run dev"

echo.
echo .
echo ========================================
echo   All services are running or launching!
echo ========================================
echo .
echo Frontend: http://127.0.0.1:5173/
echo Backend:  http://127.0.0.1:8001
echo Docs:     http://127.0.0.1:8001/docs
echo .
echo Close this window when done.
echo .

:END
pause