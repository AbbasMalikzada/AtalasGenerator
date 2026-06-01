@echo off
title Project Documentation Generator - CLI Live Run
echo ==========================================================
echo   🌐 Running Live CLI Documentation Pipeline...
echo ==========================================================
echo.

if "%~1"=="" (
    echo [USAGE] run_cli_live.bat ^<directory_with_materials^>
    echo Example: run_cli_live.bat sample_data
    echo.
    pause
    exit /b 1
)

:: Run live CLI (will read config.json defaults or environment keys)
python run_cli.py %*

echo.
echo ==========================================================
echo   Process completed.
echo ==========================================================
pause
