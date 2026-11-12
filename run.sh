#!/usr/bin/env bash
set -e
cd "$(dirname -- "${BASH_SOURCE[0]}")"

echo "============================================"
echo "  Spodo - Spotify Playlist Downloader"
echo "============================================"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python3 not found. Please install Python 3.10+."
    exit 1
fi

# Create venv if not exists
if [ ! -d "venv" ]; then
    echo "[*] Creating virtual environment..."
    python3 -m venv venv
fi

# Activate venv
source venv/bin/activate

# Install deps
echo "[*] Installing/updating dependencies..."
pip install -r requirements.txt --quiet --disable-pip-version-check

# Copy .env.example if .env doesn't exist
if [ ! -f ".env" ] && [ -f ".env.example" ]; then
    echo "[*] Copied .env.example to .env."
    cp .env.example .env
fi

echo "[*] Starting Spodo..."
echo ""
python3 main.py
