@echo off
cd /d "%~dp0"
title Spodo - Spotify Playlist Downloader
echo ============================================
echo   Spodo - Spotify Playlist Downloader
echo ============================================
echo.

:: Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.10+ from https://python.org
    pause
    exit /b 1
)

:: Create virtual environment if not exists
if not exist "venv" (
    echo [*] Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Could not create virtual environment.
        pause
        exit /b 1
    )
)

:: Activate virtual environment
call venv\Scripts\activate.bat

:: Install/upgrade dependencies
echo [*] Installing/updating dependencies...
pip install -r requirements.txt --quiet --disable-pip-version-check
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)

:: Copy .env.example to .env if .env doesn't exist
if not exist ".env" (
    if exist ".env.example" (
        echo [*] Copied .env.example to .env.
        copy .env.example .env >nul
    )
)

echo [*] Starting Spodo...
echo.
python main.py

:: Keep window open on error
if errorlevel 1 (
    echo.
    echo [ERROR] Spodo stopped unexpectedly.
    pause
)
