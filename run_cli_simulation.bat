@echo off
title Project Documentation Generator - CLI Offline Simulation
echo ==========================================================
echo   ⚡ Running CLI in Offline Simulation Mode...
echo ==========================================================
echo.

set DOCGEN_FAKE=1
python run_cli.py sample_data

echo.
echo ==========================================================
echo   Process completed.
echo ==========================================================
pause
