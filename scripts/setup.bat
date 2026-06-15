@echo off
title Ops Digital Employee - Environment Setup
cd /d "%~dp0.."

powershell -ExecutionPolicy Bypass -NoProfile -File "scripts\setup_ollama.ps1"

echo.
echo ========================================
echo   Starting services...
echo ========================================
echo.

echo [1/2] Starting backend...
start "Ops-Backend" cmd /k "cd /d "%~dp0..\backend" && uvicorn main:app --port 8001"
timeout /t 3 /nobreak >nul

echo [2/2] Starting frontend...
start "Ops-Frontend" cmd /k "cd /d "%~dp0.." && python -m http.server 5173 -d frontend"
timeout /t 2 /nobreak >nul

echo.
echo ========================================
echo   Services are running!
echo ========================================
echo.
echo Frontend: http://127.0.0.1:5173/index.html
echo Backend:  http://127.0.0.1:8001
echo Docs:     http://127.0.0.1:8001/docs
echo.
echo Close this window when done.
echo.
pause
