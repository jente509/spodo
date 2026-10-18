"""
Spodo - Internationalization (i18n) Module
Ondersteunt Nederlands (nl) en Engels (en).
"""

from typing import Dict, Any

_CURRENT_LANGUAGE = "nl"

TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "nl": {
        # Algemeen / App
        "app_title": "Spodo — Spotify Playlist Downloader",
        "public_mode": "Publieke Modus",
        "logged_in_as": "Ingelogd als {name}",
        "login_spotify": "🔑 Inloggen met Spotify",
        "logout": "Uitloggen",
        "download_dir": "📁 Downloadmap:",
        "not_set": "Niet ingesteld",
        "change_dir": "Wijzig map",
        "cookies_none": "🍪 Cookies: Geen",
        "cookies_file": "🍪 {name}",
        "cookies_browser": "🍪 {source} ({count})",
        "cookies_browser_nocount": "🍪 {source}",
        
        # Bovenbalk knoppen
        "info_btn": "ℹ️ Info",
        "about_title": "ℹ️  Over Spodo",
        "close": "Sluiten",
        "theme_toggle_tip": "Wissel licht/donker thema",
        "lang_toggle_tip": "Switch language / Wissel taal",

        # Invoersectie
        "url_placeholder": "Plak een Spotify playlist-, album- of track-URL...",
        "fetch_btn": "🔎 Ophalen",
        "fetching": "⏳ Laden...",
        "my_playlists": "📋 Mijn Playlists",
        "liked_songs": "❤️ Liked Songs",

        # Tracklijst & Selectie
        "select_all": "✅ Alles",
        "deselect_all": "❌ Geen",
        "selected_status": "{selected} van {total} geselecteerd ({duration})",
        "select_title": "Selecteer",
        "header_title": "Titel",
        "header_artist": "Artiest",
        "header_album": "Album",
        "header_duration": "Duur",

        # Onderbalk / Voortgang
        "download_btn": "⬇ Download Selectie",
        "stop_btn": "⏹ Stoppen",
        "stopping": "⏹ Stoppen...",
        "clear_log": "Wis log",
        "progress_downloaded": "{completed} / {total} gedownload",
        "progress_failed": " ({failed} mislukt)",

        # Instellingen dialoog
        "settings_title": "⚙  Spodo Instellingen",
        "sec_spotify": "Spotify API Gegevens",
        "sec_spotify_sub": "Maak een gratis app aan op developer.spotify.com voor inloggen.",
        "client_id": "Client ID:",
        "client_secret": "Client Secret:",
        "redirect_uri": "Redirect URI:",
        "sec_audio": "Formaat & Kwaliteit",
        "format_label": "Formaat:",
        "bitrate_label": "Bitrate:",
        "sec_cookies": "🍪 YouTube Cookies (Tegen Bot-blokkades)",
        "sec_cookies_sub": "Voorkomt 'Sign in to confirm you’re not a bot' fouten van YouTube.",
        "cookie_source": "Bron:",
        "cookie_help": "❓ Uitleg & Hulp",
        "sync_browser": "🔄 Synchroniseer uit {browser}",
        "syncing": "⏳ Synchroniseren...",
        "sync_saved": "✅ {count} cookies opgeslagen (werkt met open browser)",
        "sync_empty": "Klik om cookies veilig op te slaan.",
        "sync_fetching": "Bezig met ophalen...",
        "cookie_path_placeholder": "Pad naar cookies.txt...",
        "browse": "📂 Bladeren...",
        "select_cookies_file": "Selecteer cookies.txt bestand",
        "test_connection": "🔍 Test Verbinding",
        "testing_connection": "⏳ Testen...",
        "checking_connection": "Verbinding controleren...",
        "sec_ui": "Weergave & Taal",
        "language_label": "Taal:",
        "theme_label": "Thema:",
        "theme_dark": "Donker (Dark)",
        "theme_light": "Licht (Light)",
        "theme_system": "Systeem (System)",
        "save_settings": "💾  Instellingen Opslaan",

        # Cookie Hulp dialoog
        "help_dialog_title": "ℹ️  YouTube Cookies Uitleg",
        "help_dialog_heading": "🍪 Hoe gebruik je YouTube Cookies?",
        "help_dialog_text": (
            "YouTube blokkeert soms downloads als 'bot' wanneer er veel nummers\n"
            "achter elkaar worden opgevraagd. Met cookies toon je aan dat je een\n"
            "echte gebruiker bent.\n\n"
            "Optie 1: Browser-cookies (bijv. Brave / Chrome / Edge / Firefox)\n"
            "• Kies je browser in het dropdown-menu.\n"
            "• Spodo slaat je cookies veilig op in een lokaal tekstbestand.\n"
            "• Hierdoor werkt downloaden ALTIJD, zelfs terwijl je browser geopend\n"
            "  is en in gebruik is (geen vergrendelingsproblemen!).\n"
            "• Klik op 'Synchroniseer' om je cookies te vernieuwen.\n\n"
            "Optie 2: cookies.txt bestand (Alternatief)\n"
            "• Installeer in je browser de extensie 'Get cookies.txt LOCALLY'.\n"
            "• Ga naar youtube.com (terwijl je ingelogd bent) en exporteer.\n"
            "• Kies bij Bron voor 'file' en selecteer je cookies.txt bestand."
        ),
        "understood": "Begrepen",

        # Playlists picker dialoog
        "choose_playlist_title": "📋 Kies een Playlist",
        "choose_playlist_heading": "Mijn Spotify Playlists",

        # Logs & Meldingen
        "session_restored": "✅ Sessie hersteld als {name}",
        "check_ffmpeg": "🔍 FFmpeg controleren...",
        "ffmpeg_available": "✅ FFmpeg beschikbaar.",
        "ffmpeg_missing": "⚠️ FFmpeg niet gevonden — downloads kunnen mislukken.",
        "music_dir_missing": "📁 Geen muziekmap ingesteld — klik op 'Wijzig map'.",
        "cookies_loaded_file": "🍪 YouTube cookies geladen: {name} ({count} cookies)",
        "cookies_file_missing": "⚠️ YouTube cookiebestand niet gevonden — controleer Instellingen.",
        "cookies_active_browser": "🍪 YouTube cookies actief: {count} cookies uit {browser}",
        "cookies_active_browser_none": "🍪 YouTube cookies gekoppeld aan: {browser}",
        "enter_url_warn": "⚠️ Voer een Spotify-URL in.",
        "fetching_url_log": "🔍 URL ophalen: {url}",
        "tracks_loaded_log": "✅ {count} nummers geladen uit '{name}'",
        "fetch_error_log": "❌ Fout bij ophalen: {error}",
        "loading_playlists_log": "📋 Playlists ophalen...",
        "playlists_found_log": "✅ {count} playlists gevonden.",
        "playlist_error_log": "❌ Fout: {error}",
        "download_started_log": "⬇ Download gestart: {count} nummers uit '{name}'",
        "already_exists_log": "   ⏭ Bestaat al — overgeslagen",
        "converting_log": "   🔄 Converteren naar {format}...",
        "track_complete_log": "   ✅ Voltooid",
        "track_failed_log": "   ⚠️ Mislukt",
        "download_cancelled_log": "⛔ Download geannuleerd door gebruiker.",
        "download_complete_log": "✅ Klaar! {completed} gelukt, {failed} mislukt van {total} tracks.",
        "download_stopped_log": "Download gestopt. {completed} gelukt, {failed} mislukt van {total} tracks.",
        "saved_in_log": "📁 Opgeslagen in: {path}",
        "select_folder_dialog": "Selecteer downloadmap voor muziek",
        "settings_saved_log": "⚙️ Instellingen opgeslagen.",
        "empty_hint": "Plak een Spotify playlist-, album- of track-URL hierboven\nen klik op 'Ophalen' om te beginnen!",
        "ffmpeg_downloading": "⏳ FFmpeg installeren... even geduld, download loopt (~80 MB)",
        "login_ok": "✅ Ingelogd als {name}",
    },
    "en": {
        # General / App
        "app_title": "Spodo — Spotify Playlist Downloader",
        "public_mode": "Public Mode",
        "logged_in_as": "Logged in as {name}",
        "login_spotify": "🔑 Log in with Spotify",
        "logout": "Log out",
        "download_dir": "📁 Download Folder:",
        "not_set": "Not set",
        "change_dir": "Change folder",
        "cookies_none": "🍪 Cookies: None",
        "cookies_file": "🍪 {name}",
        "cookies_browser": "🍪 {source} ({count})",
        "cookies_browser_nocount": "🍪 {source}",

        # Top bar buttons
        "info_btn": "ℹ️ Info",
        "about_title": "ℹ️  About Spodo",
        "close": "Close",
        "theme_toggle_tip": "Toggle Light / Dark mode",
        "lang_toggle_tip": "Switch language / Wissel taal",

        # Input section
        "url_placeholder": "Paste a Spotify playlist, album, or track URL...",
        "fetch_btn": "🔎 Fetch",
        "fetching": "⏳ Loading...",
        "my_playlists": "📋 My Playlists",
        "liked_songs": "❤️ Liked Songs",

        # Track list & Selection
        "select_all": "✅ All",
        "deselect_all": "❌ None",
        "selected_status": "{selected} of {total} selected ({duration})",
        "select_title": "Select",
        "header_title": "Title",
        "header_artist": "Artist",
        "header_album": "Album",
        "header_duration": "Duration",

        # Bottom bar / Progress
        "download_btn": "⬇ Download Selection",
        "stop_btn": "⏹ Stop",
        "stopping": "⏹ Stopping...",
        "clear_log": "Clear log",
        "progress_downloaded": "{completed} / {total} downloaded",
        "progress_failed": " ({failed} failed)",

        # Settings dialog
        "settings_title": "⚙  Spodo Settings",
        "sec_spotify": "Spotify API Credentials",
        "sec_spotify_sub": "Create a free app on developer.spotify.com to enable user login.",
        "client_id": "Client ID:",
        "client_secret": "Client Secret:",
        "redirect_uri": "Redirect URI:",
        "sec_audio": "Format & Quality",
        "format_label": "Format:",
        "bitrate_label": "Bitrate:",
        "sec_cookies": "🍪 YouTube Cookies (Anti-Bot Bypass)",
        "sec_cookies_sub": "Prevents YouTube 'Sign in to confirm you’re not a bot' blocks.",
        "cookie_source": "Source:",
        "cookie_help": "❓ Help & Info",
        "sync_browser": "🔄 Sync from {browser}",
        "syncing": "⏳ Synchronizing...",
        "sync_saved": "✅ {count} cookies saved (works with browser open)",
        "sync_empty": "Click to safely save cookies.",
        "sync_fetching": "Fetching cookies...",
        "cookie_path_placeholder": "Path to cookies.txt...",
        "browse": "📂 Browse...",
        "select_cookies_file": "Select cookies.txt file",
        "test_connection": "🔍 Test Connection",
        "testing_connection": "⏳ Testing...",
        "checking_connection": "Testing connection...",
        "sec_ui": "Appearance & Language",
        "language_label": "Language:",
        "theme_label": "Theme:",
        "theme_dark": "Dark",
        "theme_light": "Light",
        "theme_system": "System",
        "save_settings": "💾  Save Settings",

        # Cookie Help dialog
        "help_dialog_title": "ℹ️  YouTube Cookies Guide",
        "help_dialog_heading": "🍪 How to Use YouTube Cookies?",
        "help_dialog_text": (
            "YouTube occasionally blocks automated downloads with a 'bot' challenge\n"
            "when downloading multiple songs in succession. Using cookies proves you\n"
            "are a genuine user.\n\n"
            "Option 1: Browser Cookies (e.g. Brave / Chrome / Edge / Firefox)\n"
            "• Select your browser from the dropdown menu.\n"
            "• Spodo extracts and securely caches your cookies into a local file.\n"
            "• This allows downloads to work seamlessly EVEN while your browser\n"
            "  remains open and active (no database locking issues!).\n"
            "• Click 'Sync' anytime to refresh your cookies.\n\n"
            "Option 2: cookies.txt File (Alternative)\n"
            "• Install the free browser extension 'Get cookies.txt LOCALLY'.\n"
            "• Visit youtube.com (while signed in) and export your cookies.\n"
            "• Select 'file' as Source in Spodo and browse for your cookies.txt file."
        ),
        "understood": "Understood",

        # Playlists picker dialog
        "choose_playlist_title": "📋 Choose a Playlist",
        "choose_playlist_heading": "My Spotify Playlists",

        # Logs & Notifications
        "session_restored": "✅ Session restored as {name}",
        "check_ffmpeg": "🔍 Checking FFmpeg...",
        "ffmpeg_available": "✅ FFmpeg available.",
        "ffmpeg_missing": "⚠️ FFmpeg not found — downloads might fail.",
        "music_dir_missing": "📁 No download folder set — click 'Change folder'.",
        "cookies_loaded_file": "🍪 YouTube cookies loaded: {name} ({count} cookies)",
        "cookies_file_missing": "⚠️ YouTube cookie file not found — check Settings.",
        "cookies_active_browser": "🍪 YouTube cookies active: {count} cookies from {browser}",
        "cookies_active_browser_none": "🍪 YouTube cookies linked to: {browser}",
        "enter_url_warn": "⚠️ Please enter a Spotify URL.",
        "fetching_url_log": "🔍 Fetching URL: {url}",
        "tracks_loaded_log": "✅ Loaded {count} tracks from '{name}'",
        "fetch_error_log": "❌ Error fetching: {error}",
        "loading_playlists_log": "📋 Fetching playlists...",
        "playlists_found_log": "✅ Found {count} playlists.",
        "playlist_error_log": "❌ Error: {error}",
        "download_started_log": "⬇ Download started: {count} tracks from '{name}'",
        "already_exists_log": "   ⏭ Already exists — skipped",
        "converting_log": "   🔄 Converting to {format}...",
        "track_complete_log": "   ✅ Completed",
        "track_failed_log": "   ⚠️ Failed",
        "download_cancelled_log": "⛔ Download cancelled by user.",
        "download_complete_log": "✅ Done! {completed} succeeded, {failed} failed out of {total} tracks.",
        "download_stopped_log": "Download stopped. {completed} succeeded, {failed} failed out of {total} tracks.",
        "saved_in_log": "📁 Saved in: {path}",
        "select_folder_dialog": "Select music download folder",
        "settings_saved_log": "⚙️ Settings saved.",
        "empty_hint": "Paste a Spotify playlist, album, or track URL above\nand click 'Fetch' to get started!",
        "ffmpeg_downloading": "⏳ Installing FFmpeg... please wait, download in progress (~80 MB)",
        "login_ok": "✅ Logged in as {name}",
    },
}


def get_language() -> str:
    """Geeft de actieve taalcode terug ('nl' of 'en')."""
    return _CURRENT_LANGUAGE


def set_language(lang: str) -> None:
    """Stel de actieve taal in ('nl' of 'en')."""
    global _CURRENT_LANGUAGE
    if lang in TRANSLATIONS:
        _CURRENT_LANGUAGE = lang


def t(key: str, **kwargs: Any) -> str:
    """
    Vertaal een sleutel naar de huidige taal.
    Ondersteunt formattering met kwargs (bijv. t('logged_in_as', name='Jente')).
    Valt terug naar Nederlands of de sleutel zelf indien niet gevonden.
    """
    lang_dict = TRANSLATIONS.get(_CURRENT_LANGUAGE, TRANSLATIONS["nl"])
    text = lang_dict.get(key)
    if text is None:
        text = TRANSLATIONS["nl"].get(key, key)
    if kwargs:
        try:
            return text.format(**kwargs)
        except Exception:
            return text
    return text
