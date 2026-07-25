@echo off
chcp 65001 > nul
title Account Sales Site - Local Server

cd /d "%~dp0"

echo ========================================
echo   Local Server Starting...
echo ========================================
echo.

python -c "import fastapi, uvicorn" 2>nul
if errorlevel 1 (
    echo [First time] Installing packages...
    pip install -r requirements.txt
    echo.
)

echo Starting server...
echo.
echo   Public  : http://127.0.0.1:8000/
echo   Admin   : http://127.0.0.1:8000/admin
echo.
echo Press Ctrl + C to stop
echo ========================================
echo.

start "" "http://127.0.0.1:8000/admin"

python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000

echo.
echo Server stopped.
pause
