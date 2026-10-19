"""
Spodo - Configuratiebeheer
Slaat app-instellingen op in ~/.spodo/config.json en detecteert de standaard muziekmap.
"""

import json
import os
import shutil
from pathlib import Path

from dotenv import load_dotenv

def _determine_config_dir() -> Path:
    """
    Bepaalt een betrouwbare, schrijfbare configuratiemap voor Spodo.
    1. Controleert eerst ~/.spodo (indien al bestaand en schrijfbaar).
    2. Probeert ~/.spodo aan te maken (standaard gedrag).
    3. Op Windows: gebruikt %APPDATA%/spodo (voorkomt WinError 5 Toegang geweigerd in C:\\Users\\<user>).
    4. Lokale projectmap fallback (.spodo) als uiterste redmiddel.
    """
    # 1. Probeer ~/.spodo
    home_candidate = Path.home() / ".spodo"
    try:
        home_candidate.mkdir(parents=True, exist_ok=True)
        test_file = home_candidate / ".write_test"
        test_file.touch()
        test_file.unlink()
        return home_candidate
    except (PermissionError, OSError):
        pass

    # 2. Windows: gebruik APPDATA of LOCALAPPDATA
    appdata = os.getenv("APPDATA") or os.getenv("LOCALAPPDATA")
    if appdata:
        appdata_candidate = Path(appdata) / "spodo"
        try:
            appdata_candidate.mkdir(parents=True, exist_ok=True)
            test_file = appdata_candidate / ".write_test"
            test_file.touch()
            test_file.unlink()
            return appdata_candidate
        except (PermissionError, OSError):
            pass

    # 3. Lokale fallback
    local_dir = Path(__file__).resolve().parent / ".spodo"
    try:
        local_dir.mkdir(parents=True, exist_ok=True)
        return local_dir
    except (PermissionError, OSError):
        pass

    return home_candidate


CONFIG_DIR = _determine_config_dir()

# Migreer eventuele instellingen of ffmpeg uit legacy mappen
legacy_candidates = [
    Path.home() / ".spooty",
    (Path(os.getenv("APPDATA")) / "spooty") if os.getenv("APPDATA") else None,
    (Path.home() / ".spodo") if CONFIG_DIR != (Path.home() / ".spodo") else None,
]
for leg_dir in legacy_candidates:
    if leg_dir and leg_dir.exists() and leg_dir.is_dir() and leg_dir != CONFIG_DIR:
        try:
            for item in leg_dir.iterdir():
                target = CONFIG_DIR / item.name
                if not target.exists():
                    if item.is_dir():
                        shutil.copytree(item, target)
                    else:
                        shutil.copy2(item, target)
        except Exception:
            pass

# Laad .env uit huidige map en uit configuratiemappen
load_dotenv()
load_dotenv(CONFIG_DIR / ".env")
for leg_dir in legacy_candidates:
    if leg_dir:
        load_dotenv(leg_dir / ".env")

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
    "concurrent_downloads": 2,
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
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    except (PermissionError, OSError):
        pass

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

    # Filter placeholder waarden uit opgeslagen config
    if cfg.get("client_id") in ("your_client_id_here", "jouw_client_id_hier"):
        cfg["client_id"] = ""
    if cfg.get("client_secret") in ("your_client_secret_here", "jouw_client_secret_hier"):
        cfg["client_secret"] = ""

    # Env-variabelen hebben hoogste prioriteit (mits geen placeholders)
    env_id = (os.getenv("SPOTIFY_CLIENT_ID") or "").strip()
    env_secret = (os.getenv("SPOTIFY_CLIENT_SECRET") or "").strip()
    if env_id and env_id not in ("your_client_id_here", "jouw_client_id_hier"):
        cfg["client_id"] = env_id
    if env_secret and env_secret not in ("your_client_secret_here", "jouw_client_secret_hier"):
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
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, "w", encoding="utf-8") as fh:
            json.dump(cfg, fh, indent=2, ensure_ascii=False)
    except (PermissionError, OSError) as exc:
        print(f"[WAARSCHUWING] Kon configuratie niet opslaan naar {CONFIG_FILE}: {exc}")


def get_config_value(key: str, default=None):
    """Lees een losse waarde uit de opgeslagen configuratie."""
    cfg = load_config()
    return cfg.get(key, default)
