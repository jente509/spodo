"""
Spodo - Download Engine
Gebruikt yt-dlp voor YouTube-zoeken & downloaden, en mutagen voor ID3-tagging
met Spotify-metadata (titel, artiest, album, track#, albumcover).
"""

import os
import re
import shutil
import subprocess
import sys
import threading
import urllib.parse
import urllib.request
import zipfile
import io
from pathlib import Path
from typing import Callable, Optional

import requests
import yt_dlp
from yt_dlp.utils import remove_terminal_sequences
from mutagen.id3 import ID3, TIT2, TPE1, TALB, APIC, TRCK, TDRC
from mutagen.mp3 import MP3
from mutagen.mp4 import MP4, MP4Cover
from mutagen.flac import FLAC, Picture as FLACPicture

from config import CONFIG_DIR
from i18n import t

FFMPEG_DIR = CONFIG_DIR / "ffmpeg"

# Windows: verberg subprocess-consolevensters
_CREATION_FLAGS = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0


# ══════════════════════════════════════════════════════════════════
# FFmpeg detectie & installatie
# ══════════════════════════════════════════════════════════════════

def _inject_ffmpeg_to_path(ffmpeg_bin_dir: Path) -> None:
    """Voeg ffmpeg-map toe aan os.environ['PATH'] voor het huidige proces en alle subprocessen."""
    try:
        dir_str = str(ffmpeg_bin_dir.resolve())
        current_path = os.environ.get("PATH", "")
        # Voorkom dubbele toevoegingen
        paths = current_path.split(os.pathsep)
        if dir_str not in paths:
            os.environ["PATH"] = dir_str + os.pathsep + current_path

        # Op Windows: probeer ook persistently toe te voegen aan User PATH via PowerShell/SetEnvironmentVariable
        if sys.platform == "win32":
            try:
                import winreg
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment", 0, winreg.KEY_READ | winreg.KEY_WRITE) as key:
                    try:
                        user_path, _ = winreg.QueryValueEx(key, "Path")
                    except FileNotFoundError:
                        user_path = ""
                    user_paths = [p for p in user_path.split(";") if p]
                    if dir_str not in user_paths:
                        user_paths.append(dir_str)
                        winreg.SetValueEx(key, "Path", 0, winreg.REG_EXPAND_SZ, ";".join(user_paths))
            except Exception:
                pass
    except Exception:
        pass


def find_ffmpeg() -> Optional[str]:
    """Zoek ffmpeg in PATH of in ~/.spodo/ffmpeg/ (of legacy ~/.spooty/ffmpeg/)."""
    # 1. Lokale Spodo map eerst controleren en direct aan proces-PATH toevoegen
    local = FFMPEG_DIR / ("ffmpeg.exe" if sys.platform == "win32" else "ffmpeg")
    if local.exists():
        _inject_ffmpeg_to_path(FFMPEG_DIR)
        return str(local)

    legacy = Path.home() / ".spooty" / "ffmpeg" / ("ffmpeg.exe" if sys.platform == "win32" else "ffmpeg")
    if legacy.exists():
        _inject_ffmpeg_to_path(legacy.parent)
        return str(legacy)

    which = shutil.which("ffmpeg")
    if which:
        return which

    return None


def download_ffmpeg(on_log: Optional[Callable[[str], None]] = None) -> Optional[str]:
    """Download een statische ffmpeg-build naar ~/.spodo/ffmpeg/ (alleen Windows)."""
    if sys.platform != "win32":
        if on_log:
            on_log("⚠️ Automatische ffmpeg-download is alleen beschikbaar op Windows.")
            on_log("   Installeer ffmpeg handmatig: https://ffmpeg.org/download.html")
        return None

    FFMPEG_DIR.mkdir(parents=True, exist_ok=True)
    url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"

    if on_log:
        on_log("⏳ FFmpeg downloaden (~80 MB)... dit kan even duren.")

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Spodo/1.0"})
        with urllib.request.urlopen(req, timeout=600) as response:
            total = int(response.headers.get("Content-Length", 0))
            data = bytearray()
            chunk_size = 1024 * 1024  # 1 MB
            last_pct = -10

            while True:
                chunk = response.read(chunk_size)
                if not chunk:
                    break
                data.extend(chunk)
                if on_log and total:
                    pct = int(len(data) / total * 100)
                    if pct >= last_pct + 10:
                        on_log(f"   ⬇ {len(data) // (1024 * 1024)} MB / {total // (1024 * 1024)} MB ({pct}%)")
                        last_pct = pct

        if on_log:
            on_log("📦 FFmpeg uitpakken...")

        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            for member in zf.namelist():
                basename = os.path.basename(member)
                if basename in ("ffmpeg.exe", "ffprobe.exe"):
                    target = FFMPEG_DIR / basename
                    with zf.open(member) as src, open(target, "wb") as dst:
                        dst.write(src.read())

        ffmpeg_exe = FFMPEG_DIR / "ffmpeg.exe"
        if ffmpeg_exe.exists():
            _inject_ffmpeg_to_path(FFMPEG_DIR)
            if on_log:
                on_log(f"✅ FFmpeg geïnstalleerd en geactiveerd in {FFMPEG_DIR}")
            return str(ffmpeg_exe)
        else:
            if on_log:
                on_log("❌ FFmpeg uitpakken mislukt — bestanden niet gevonden in zip.")
            return None

    except Exception as exc:
        if on_log:
            on_log(f"❌ FFmpeg download mislukt: {exc}")
        return None


def ensure_ffmpeg(on_log: Optional[Callable[[str], None]] = None) -> Optional[str]:
    """Zoek ffmpeg of download het automatisch. Retourneert pad of None."""
    path = find_ffmpeg()
    if path:
        if on_log:
            on_log(f"✅ FFmpeg gevonden: {path}")
        return path
    return download_ffmpeg(on_log)


# ══════════════════════════════════════════════════════════════════
# Helper functies
# ══════════════════════════════════════════════════════════════════

_INVALID_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def _sanitize_filename(name: str) -> str:
    """Verwijder ongeldige tekens uit bestandsnamen."""
    cleaned = _INVALID_CHARS.sub("", name).strip(". ")
    return cleaned[:200] if cleaned else "unknown"


def _clean_ansi(text: str) -> str:
    """Verwijder ANSI escape-sequenties uit tekst voor schone weergave in de UI."""
    if not text:
        return ""
    try:
        text = remove_terminal_sequences(text)
    except Exception:
        pass
    return re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', text)


def _find_js_runtime() -> dict:
    """Detecteer of Node.js, Deno of Bun beschikbaar is voor yt-dlp JS challenges."""
    for bin_name in ("node", "deno", "bun"):
        which = shutil.which(bin_name)
        if which:
            return {bin_name: {}}
    if sys.platform == "win32":
        for cand in (
            Path(r"C:\Program Files\nodejs\node.exe"),
            Path(r"C:\Program Files (x86)\nodejs\node.exe"),
        ):
            if cand.exists():
                return {"node": {"path": str(cand)}}
    return {}


def _generate_candidate_queries(artists: str, title: str) -> list[str]:
    """Genereer geordende zoekopdrachten voor YouTube Music en YouTube."""
    main_query = f"{artists} - {title}".strip()
    encoded = urllib.parse.quote_plus(main_query)
    queries = [
        # 1. YouTube Music: officiële album-/studiotrack, geen censuur op gevoelige songtitels, geen leeftijdsmuren
        f"https://music.youtube.com/search?q={encoded}#songs",
        # 2. YouTube audio zoekopdracht
        f"ytsearch1:{main_query} audio",
        # 3. Directe YouTube zoekopdracht
        f"ytsearch1:{main_query}",
    ]

    # 4. Als titel toevoegingen heeft zoals (feat. ...), (Remix), - Bonus Track, etc.:
    # Bied ook een vereenvoudigde variant aan als fallback
    clean_title = re.sub(r'\(.*?\)|\[.*?\]', '', title).strip()
    clean_title = re.sub(
        r'\s*-\s*(?:remaster(?:ed)?(?:\s*\d+)?|bonus(?:\s*track)?|from\s+.*?|single\s*version|original\s*version).*$',
        '',
        clean_title,
        flags=re.IGNORECASE,
    ).strip()
    if clean_title and clean_title.lower() != title.lower():
        clean_query = f"{artists} - {clean_title}".strip()
        clean_encoded = urllib.parse.quote_plus(clean_query)
        queries.extend([
            f"https://music.youtube.com/search?q={clean_encoded}#songs",
            f"ytsearch1:{clean_query} audio",
            f"ytsearch1:{clean_query}",
        ])

    seen = set()
    unique_queries = []
    for q in queries:
        if q not in seen:
            seen.add(q)
            unique_queries.append(q)
    return unique_queries


# ══════════════════════════════════════════════════════════════════
# ID3 / metadata tagging
# ══════════════════════════════════════════════════════════════════

def _fetch_album_art(url: str, cache: dict) -> Optional[bytes]:
    """Download albumcover-bytes (met simpele cache per URL)."""
    if not url:
        return None
    if url in cache:
        return cache[url]
    try:
        resp = requests.get(url, timeout=15)
        if resp.status_code == 200:
            cache[url] = resp.content
            return resp.content
    except Exception:
        pass
    cache[url] = None
    return None


def _tag_mp3(filepath: Path, track: dict, art_data: Optional[bytes]) -> None:
    """Voeg ID3-tags en albumcover toe aan een MP3-bestand."""
    try:
        audio = MP3(filepath)
    except Exception:
        return
    if audio.tags is None:
        audio.add_tags()

    audio.tags.add(TIT2(encoding=3, text=track.get("name", "")))
    audio.tags.add(TPE1(encoding=3, text=track.get("artists", "")))
    audio.tags.add(TALB(encoding=3, text=track.get("album", "")))
    tn = track.get("track_number")
    if tn:
        audio.tags.add(TRCK(encoding=3, text=str(tn)))
    rd = track.get("release_date")
    if rd:
        audio.tags.add(TDRC(encoding=3, text=rd))
    if art_data:
        audio.tags.add(APIC(encoding=3, mime="image/jpeg", type=3, desc="Cover", data=art_data))
    audio.save()


def _tag_flac(filepath: Path, track: dict, art_data: Optional[bytes]) -> None:
    """Voeg VorbisComment-tags en albumcover toe aan een FLAC-bestand."""
    try:
        audio = FLAC(filepath)
    except Exception:
        return
    audio["title"] = track.get("name", "")
    audio["artist"] = track.get("artists", "")
    audio["album"] = track.get("album", "")
    tn = track.get("track_number")
    if tn:
        audio["tracknumber"] = str(tn)
    rd = track.get("release_date")
    if rd:
        audio["date"] = rd
    if art_data:
        pic = FLACPicture()
        pic.type = 3
        pic.mime = "image/jpeg"
        pic.desc = "Cover"
        pic.data = art_data
        audio.clear_pictures()
        audio.add_picture(pic)
    audio.save()


def _tag_m4a(filepath: Path, track: dict, art_data: Optional[bytes]) -> None:
    """Voeg MP4-atoms toe aan een M4A/AAC-bestand."""
    try:
        audio = MP4(filepath)
    except Exception:
        return
    audio["\xa9nam"] = [track.get("name", "")]
    audio["\xa9ART"] = [track.get("artists", "")]
    audio["\xa9alb"] = [track.get("album", "")]
    tn = track.get("track_number")
    if tn:
        audio["trkn"] = [(tn, 0)]
    rd = track.get("release_date")
    if rd:
        audio["\xa9day"] = [rd]
    if art_data:
        audio["covr"] = [MP4Cover(art_data, imageformat=MP4Cover.FORMAT_JPEG)]
    audio.save()


def _tag_file(filepath: Path, track: dict, fmt: str, art_data: Optional[bytes]) -> None:
    """Dispatch naar het juiste tagging-formaat."""
    taggers = {
        "mp3": _tag_mp3,
        "flac": _tag_flac,
        "m4a": _tag_m4a,
    }
    tagger = taggers.get(fmt)
    if tagger:
        tagger(filepath, track, art_data)


# ══════════════════════════════════════════════════════════════════
# YouTube Cookie beheer (veilig voor geopende browsers)
# ══════════════════════════════════════════════════════════════════

def get_saved_cookie_count(filepath: Optional[Path] = None) -> int:
    """Tel het aantal geldige cookies in een cookies.txt bestand."""
    path = filepath or (CONFIG_DIR / "youtube_cookies.txt")
    if not path.exists():
        return 0
    try:
        count = 0
        with open(path, "r", encoding="utf-8", errors="ignore") as fh:
            for line in fh:
                line = line.strip()
                if line and not line.startswith("#"):
                    count += 1
        return count
    except Exception:
        return 0


def sync_browser_cookies(browser_name: str) -> tuple[bool, str, int]:
    """
    Haal cookies op uit de opgegeven browser en sla ze op in ~/.spodo/youtube_cookies.txt.
    Retourneert (succes: bool, bericht: str, cookie_aantal: int).
    """
    b_name = (browser_name or "").strip().lower()
    if b_name in ("", "none", "file"):
        return False, "Geen browser geselecteerd.", 0

    target_path = CONFIG_DIR / "youtube_cookies.txt"
    try:
        from yt_dlp.cookies import extract_cookies_from_browser
        jar = extract_cookies_from_browser(b_name)
        if jar and len(jar) > 0:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            jar.save(str(target_path), ignore_discard=True, ignore_expires=True)
            count = get_saved_cookie_count(target_path)
            return True, f"{count} cookies succesvol opgeslagen uit {b_name.capitalize()}.", count
        return False, f"Geen cookies gevonden in {b_name.capitalize()}.", 0
    except Exception as exc:
        err = _clean_ansi(str(exc))
        existing = get_saved_cookie_count(target_path)
        if "Could not copy" in err or "Permission denied" in err or "13" in err:
            if existing > 0:
                msg = f"{b_name.capitalize()} staat open. Bestaande {existing} cookies blijven actief!"
                return True, msg, existing
            msg = f"{b_name.capitalize()} staat open en vergrendelt cookies. Sluit de browser even af om te synchroniseren."
        else:
            msg = f"Kon cookies niet ophalen uit {b_name.capitalize()}: {err[:80]}"
        return False, msg, existing


def resolve_cookie_opts(cookie_source: str = "none", cookie_file: str = "") -> dict:
    """
    Bepaalt de yt-dlp cookie-instellingen.
    Geeft ALTIJD voorrang aan het opgeslagen cookies.txt bestand zodat er nooit
    vergrendelingsconflicten ('Could not copy Chrome cookie database') optreden
    wanneer de browser geopend is.
    """
    source = (cookie_source or "none").lower()
    default_cookies = CONFIG_DIR / "youtube_cookies.txt"

    # 1. Specifiek gekozen cookies.txt bestand
    if source == "file" and cookie_file and Path(cookie_file).exists():
        return {"cookiefile": str(cookie_file)}

    # 2. Browser gekozen (bijv. Brave, Chrome, Edge, Firefox)
    if source in ("brave", "chrome", "edge", "firefox", "opera", "safari", "vivaldi"):
        # Als het opgeslagen bestand al bestaat en cookies bevat: direct gebruiken!
        # Dit voorkomt 100% dat yt-dlp het gelockte browserbestand probeert te kopiëren.
        if default_cookies.exists() and default_cookies.stat().st_size > 0:
            return {"cookiefile": str(default_cookies)}

        # Bestand bestaat nog niet: probeer het eenmalig te extraheren
        try:
            from yt_dlp.cookies import extract_cookies_from_browser
            jar = extract_cookies_from_browser(source)
            if jar and len(jar) > 0:
                default_cookies.parent.mkdir(parents=True, exist_ok=True)
                jar.save(str(default_cookies), ignore_discard=True, ignore_expires=True)
                return {"cookiefile": str(default_cookies)}
        except Exception:
            pass

        # Als extraheren mislukt (bijv. browser open) en er was nog geen bestand:
        return {"cookiesfrombrowser": (source,)}

    # 3. Geen browser gekozen ('none'), maar standaard cookiebestand is wel aanwezig
    if default_cookies.exists() and default_cookies.stat().st_size > 0:
        return {"cookiefile": str(default_cookies)}

    return {}


# ══════════════════════════════════════════════════════════════════
# Downloader klasse
# ══════════════════════════════════════════════════════════════════

class Downloader:
    """Download Spotify-tracks via yt-dlp + mutagen met real-time voortgang."""

    def __init__(
        self,
        music_dir: str,
        output_format: str = "mp3",
        bitrate: str = "320k",
        cookie_source: str = "none",
        cookie_file: str = "",
    ):
        self.music_dir = music_dir
        self.output_format = output_format
        self.bitrate = bitrate
        self.cookie_source = (cookie_source or "none").lower()
        self.cookie_file = cookie_file or ""
        self._cancel_event = threading.Event()
        self._ffmpeg_path = find_ffmpeg()
        self._art_cache: dict[str, Optional[bytes]] = {}
        self._cookie_opts = resolve_cookie_opts(self.cookie_source, self.cookie_file)

    def cancel(self) -> None:
        """Annuleer de lopende download."""
        self._cancel_event.set()

    @property
    def is_cancelled(self) -> bool:
        return self._cancel_event.is_set()

    # ------------------------------------------------------------------
    # Eén track downloaden
    # ------------------------------------------------------------------

    def _download_single(
        self,
        track: dict,
        output_dir: Path,
        on_log: Optional[Callable[[str], None]] = None,
    ) -> bool:
        """Download en tag één track. Retourneert True bij succes."""
        artists = track.get("artists", "Onbekend")
        title = track.get("name", "Onbekend")
        safe_name = _sanitize_filename(f"{artists} - {title}")
        final_path = output_dir / f"{safe_name}.{self.output_format}"

        # Sla over als bestand al bestaat
        if final_path.exists():
            if on_log:
                on_log(t("already_exists_log"))
            return True

        # Escape %-tekens in de template zodat yt-dlp ze niet interpreteert
        safe_outtmpl = safe_name.replace("%", "%%")
        outtmpl = str(output_dir / f"{safe_outtmpl}.%(ext)s")

        bitrate_num = self.bitrate.rstrip("k") if self.bitrate else "320"

        progress_state = {"last_pct": ""}

        def _progress_hook(d: dict) -> None:
            if self._cancel_event.is_set():
                raise yt_dlp.utils.DownloadCancelled("Geannuleerd door gebruiker")
            if d.get("status") == "downloading" and on_log:
                raw_pct = d.get("_percent_str", "")
                pct = _clean_ansi(raw_pct).strip()
                if pct and pct != progress_state["last_pct"]:
                    speed = _clean_ansi(d.get("_speed_str", "")).strip()
                    on_log(f"   ⬇ {pct}  {speed}")
                    progress_state["last_pct"] = pct
            elif d.get("status") == "finished" and on_log:
                on_log(t("converting_log", format=self.output_format))

        ydl_opts: dict = {
            "format": "bestaudio/best",
            "playlist_items": "1",
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": self.output_format,
                    "preferredquality": bitrate_num,
                }
            ],
            "outtmpl": {"default": outtmpl},
            "quiet": True,
            "no_warnings": True,
            "no_color": True,
            "progress_hooks": [_progress_hook],
            "noplaylist": False,
            "retries": 5,
            "fragment_retries": 5,
            "file_access_retries": 3,
            "socket_timeout": 30,
        }

        if self._ffmpeg_path:
            ydl_opts["ffmpeg_location"] = str(Path(self._ffmpeg_path).parent)

        js_runtimes = _find_js_runtime()
        if js_runtimes:
            ydl_opts["js_runtimes"] = js_runtimes
            ydl_opts["remote_components"] = {"ejs:github"}

        # Cookies toevoegen indien geconfigureerd
        if self._cookie_opts:
            ydl_opts.update(self._cookie_opts)

        candidate_queries = _generate_candidate_queries(artists, title)
        downloaded = False
        last_error = None
        cookie_warned = False

        for query in candidate_queries:
            if self._cancel_event.is_set():
                return False

            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([query])

                if final_path.exists():
                    downloaded = True
                    break
            except yt_dlp.utils.DownloadCancelled:
                return False
            except Exception as exc:
                last_error = exc
                err_text = str(exc)
                if not cookie_warned and on_log and ("Could not copy" in err_text or "Permission denied" in err_text) and "cookie" in err_text.lower():
                    on_log(f"   ⚠️ {self.cookie_source.capitalize()} staat momenteel open en vergrendelt cookies.")
                    on_log("      Sluit je browser even af, of importeer een cookies.txt bestand via Instellingen.")
                    cookie_warned = True
                continue

        # Als het bestand niet is aangemaakt, ruim eventuele tijdelijke bestanden op
        if not downloaded or not final_path.exists():
            for leftover in output_dir.glob(f"{safe_name}.*"):
                if leftover.suffix in (".part", ".ytdl", ".temp"):
                    try:
                        leftover.unlink(missing_ok=True)
                    except Exception:
                        pass

            if on_log:
                if last_error:
                    clean_err = _clean_ansi(str(last_error)).strip()
                    on_log(f"   ❌ Fout: {clean_err}")
                else:
                    on_log(f"   ⚠️ Nummer niet gevonden op YouTube / YouTube Music")
            return False

        # Tagging met Spotify-metadata + albumcover
        art_data = _fetch_album_art(track.get("album_art", ""), self._art_cache)
        _tag_file(final_path, track, self.output_format, art_data)

        return True

    # ------------------------------------------------------------------
    # Meerdere tracks downloaden
    # ------------------------------------------------------------------

    def download_tracks(
        self,
        tracks: list[dict],
        collection_name: str,
        on_progress: Optional[Callable[[int, int, int], None]] = None,
        on_log: Optional[Callable[[str], None]] = None,
        on_complete: Optional[Callable[[int, int, int], None]] = None,
    ) -> None:
        """
        Download een lijst tracks.

        Parameters
        ----------
        tracks : lijst van track-dicts (Spotify-metadata)
        collection_name : naam van de playlist/album (wordt submap)
        on_progress : callback(completed, failed, total) — per track
        on_log : callback(message) — log-regels
        on_complete : callback(completed, failed, total) — als alles klaar is
        """
        self._cancel_event.clear()
        self._art_cache.clear()

        if not self._ffmpeg_path:
            self._ffmpeg_path = find_ffmpeg()
        if not self._ffmpeg_path:
            self._ffmpeg_path = ensure_ffmpeg(on_log)

        total = len(tracks)
        completed = 0
        failed = 0

        safe_folder = _sanitize_filename(collection_name) or "Downloads"
        output_dir = Path(self.music_dir) / safe_folder
        output_dir.mkdir(parents=True, exist_ok=True)

        self._cookie_opts = resolve_cookie_opts(self.cookie_source, self.cookie_file)
        if "cookiefile" in self._cookie_opts and on_log:
            c_path = Path(self._cookie_opts["cookiefile"])
            count = get_saved_cookie_count(c_path)
            if count > 0:
                on_log(f"🍪 YouTube cookies actief: {count} cookies ({c_path.name})")
            else:
                on_log(f"🍪 YouTube cookiebestand actief: {c_path.name}")

        for index, track in enumerate(tracks, start=1):
            if self._cancel_event.is_set():
                if on_log:
                    on_log(t("download_cancelled_log"))
                break

            display = f"{track.get('artists', '?')} - {track.get('name', '?')}"
            if on_log:
                on_log(f"▶ [{index}/{total}] {display}")

            success = self._download_single(track, output_dir, on_log)

            if self._cancel_event.is_set():
                break

            if success:
                completed += 1
                if on_log:
                    on_log(t("track_complete_log"))
            else:
                failed += 1
                if on_log:
                    on_log(t("track_failed_log"))

            if on_progress:
                on_progress(completed, failed, total)

        # Eindrapport
        if on_log:
            on_log("─" * 50)
            if self._cancel_event.is_set():
                on_log(t("download_stopped_log", completed=completed, failed=failed, total=total))
            else:
                on_log(t("download_complete_log", completed=completed, failed=failed, total=total))
            on_log(t("saved_in_log", path=str(output_dir)))

        if on_complete:
            on_complete(completed, failed, total)


def test_youtube_auth(cookie_source: str = "none", cookie_file: str = "") -> tuple[bool, str]:
    """Test of YouTube-toegang werkt met de opgegeven cookie-instelling."""
    cookie_source = (cookie_source or "none").lower()
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "socket_timeout": 15,
    }
    js_runtimes = _find_js_runtime()
    if js_runtimes:
        ydl_opts["js_runtimes"] = js_runtimes
        ydl_opts["remote_components"] = {"ejs:github"}

    cookie_opts = resolve_cookie_opts(cookie_source, cookie_file)
    ydl_opts.update(cookie_opts)

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info("https://www.youtube.com/watch?v=ggG9ySCChYw", download=False)
            if info and info.get("title"):
                cookie_desc = ""
                if "cookiefile" in cookie_opts:
                    c_count = get_saved_cookie_count(Path(cookie_opts["cookiefile"]))
                    cookie_desc = f" ({c_count} cookies actief)" if c_count else " (bestand actief)"
                elif "cookiesfrombrowser" in cookie_opts:
                    cookie_desc = f" ({cookie_source.capitalize()} actief)"
                return True, f"Verbinding geslaagd!{cookie_desc}"
            return False, "Geen metadata ontvangen."
    except Exception as exc:
        err = _clean_ansi(str(exc))
        if "Could not copy" in err or "Permission denied" in err:
            return False, f"{cookie_source.capitalize()} staat momenteel open. Sluit de browser even af of gebruik een cookies.txt bestand."
        if "Sign in to confirm you’re not a bot" in err:
            return False, "YouTube vraagt om authenticatie. Gebruik cookies.txt of log in via browser."
        return False, err[:120]
