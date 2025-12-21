@echo off
REM Batch script to run OLX scraper
REM This script ensures Python is in PATH and runs the scraper

cd /d "%~dp0"
python scraper.py

REM Keep window open if there's an error (optional - remove if you want it to close)
if errorlevel 1 (
    echo.
    echo Scraper encountered an error. Press any key to close...
    pause >nul
)

