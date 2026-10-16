@echo off
title Spodo - Spotify Playlist Downloader
echo ============================================
echo   Spodo - Spotify Playlist Downloader
echo ============================================
echo.

:: Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo [FOUT] Python is niet gevonden. Installeer Python 3.10+ van https://python.org
    pause
    exit /b 1
)

:: Create virtual environment if not exists
if not exist "venv" (
    echo [*] Virtuele omgeving aanmaken...
    python -m venv venv
    if errorlevel 1 (
        echo [FOUT] Kon virtuele omgeving niet aanmaken.
        pause
        exit /b 1
    )
)

:: Activate virtual environment
call venv\Scripts\activate.bat

:: Install/upgrade dependencies
echo [*] Dependencies installeren/updaten...
pip install -r requirements.txt --quiet --disable-pip-version-check
if errorlevel 1 (
    echo [FOUT] Kon dependencies niet installeren.
    pause
    exit /b 1
)

:: Copy .env.example to .env if .env doesn't exist
if not exist ".env" (
    if exist ".env.example" (
        echo [*] .env.example gekopieerd naar .env - vul je Spotify credentials in.
        copy .env.example .env >nul
    )
)

echo [*] Spodo starten...
echo.
python main.py

:: Keep window open on error
if errorlevel 1 (
    echo.
    echo [FOUT] Spodo is onverwacht gestopt.
    pause
)
