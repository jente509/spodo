#!/usr/bin/env bash
set -e
cd "$(dirname -- "${BASH_SOURCE[0]}")"

echo "============================================"
echo "  Spodo - Spotify Playlist Downloader"
echo "============================================"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "[FOUT] Python3 is niet gevonden. Installeer Python 3.10+."
    exit 1
fi

# Create venv if not exists
if [ ! -d "venv" ]; then
    echo "[*] Virtuele omgeving aanmaken..."
    python3 -m venv venv
fi

# Activate venv
source venv/bin/activate

# Install deps
echo "[*] Dependencies installeren/updaten..."
pip install -r requirements.txt --quiet --disable-pip-version-check

# Copy .env.example if .env doesn't exist
if [ ! -f ".env" ] && [ -f ".env.example" ]; then
    echo "[*] .env.example gekopieerd naar .env - vul je Spotify credentials in."
    cp .env.example .env
fi

echo "[*] Spodo starten..."
echo ""
python3 main.py
