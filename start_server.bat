@echo off
title Project Documentation Generator - Uvicorn Server
echo ==========================================================
echo   🚀 Launching Project Documentation Generator Server...
echo ==========================================================
echo.

:: Verify Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in your PATH.
    echo Please install Python 3.9+ and try again.
    pause
    exit /b 1
)

:: Start Uvicorn Server
echo Server starting on http://127.0.0.1:8000
echo Close this window to stop the server.
echo.
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Server failed to start. Please verify python-multipart is installed.
    echo Running: pip install python-multipart uvicorn fastapi pydantic requests
    pause
)
