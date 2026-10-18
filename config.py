"""
Spodo - Configuratiebeheer
Slaat app-instellingen op in ~/.spodo/config.json en detecteert de standaard muziekmap.
"""

import json
import os
import shutil
from pathlib import Path

from dotenv import load_dotenv

CONFIG_DIR = Path.home() / ".spodo"
LEGACY_CONFIG_DIR = Path.home() / ".spooty"

# Migreer eventuele instellingen of ffmpeg uit legacy ~/.spooty map
if LEGACY_CONFIG_DIR.exists() and not CONFIG_DIR.exists():
    try:
        shutil.copytree(LEGACY_CONFIG_DIR, CONFIG_DIR)
    except Exception:
        pass

# Laad .env uit huidige map en uit ~/.spodo/
load_dotenv()
load_dotenv(CONFIG_DIR / ".env")
load_dotenv(LEGACY_CONFIG_DIR / ".env")

CONFIG_FILE = CONFIG_DIR / "config.json"
SPOTIFY_CACHE_PATH = str(CONFIG_DIR / ".spotify_cache")

DEFAULT_CLIENT_ID = ""
DEFAULT_CLIENT_SECRET = ""

DEFAULT_CONFIG = {
    "music_dir": "",
    "client_id": "",
    "client_secret": "",
    "output_format": "mp3",
    "bitrate": "320k",
    "redirect_uri": "http://127.0.0.1:3001/api/callback",
    "cookie_source": "none",
    "cookie_file": "",
    "language": "nl",
    "appearance_mode": "dark",
}


def _detect_music_dir() -> str:
    """Detecteer de standaard muziekmap (Music of Muziek)."""
    for name in ("Music", "Muziek"):
        candidate = Path.home() / name
        if candidate.is_dir():
            return str(candidate)
    return ""


def load_config() -> dict:
    """Laad configuratie uit config.json, samengevoegd met standaardwaarden en env-variabelen."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    cfg = DEFAULT_CONFIG.copy()

    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as fh:
                stored = json.load(fh)
            for key, value in stored.items():
                if value is not None:  # Overschrijf alleen als de opgeslagen waarde niet None is (behoudt False/0)
                    cfg[key] = value
        except (json.JSONDecodeError, IOError):
            pass  # Corrupte config → gebruik defaults

    # Env-variabelen hebben hoogste prioriteit
    env_id = os.getenv("SPOTIFY_CLIENT_ID")
    env_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    if env_id:
        cfg["client_id"] = env_id
    if env_secret:
        cfg["client_secret"] = env_secret

    # Auto-detectie muziekmap als nog niet geconfigureerd
    if not cfg["music_dir"] or not Path(cfg["music_dir"]).is_dir():
        detected = _detect_music_dir()
        if detected:
            cfg["music_dir"] = detected

    save_config(cfg)
    return cfg


def save_config(cfg: dict) -> None:
    """Sla configuratie op naar config.json."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as fh:
        json.dump(cfg, fh, indent=2, ensure_ascii=False)


def get_config_value(key: str, default=None):
    """Lees een losse waarde uit de opgeslagen configuratie."""
    cfg = load_config()
    return cfg.get(key, default)
