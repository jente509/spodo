"""
Spodo - Strings & Localization (English only)
"""

from typing import Dict, Any

_CURRENT_LANGUAGE = "en"

STRINGS: Dict[str, str] = {
    # General / App
    "app_title": "Spodo — Spotify Playlist Downloader",
    "public_mode": "Public Mode",
    "logged_in_as": "Logged in as {name}",
    "login_spotify": "🔑 Log in with Spotify",
    "logout": "Log out",
    "download_dir": "📁 Download Folder:",
    "not_set": "Not set",
    "change_dir": "Change folder",
    "open_folder": "📂 Open Folder",
    "cookies_none": "🍪 Cookies: None",
    "cookies_file": "🍪 {name}",
    "cookies_browser": "🍪 {source} ({count})",
    "cookies_browser_nocount": "🍪 {source}",

    # Top bar buttons
    "info_btn": "ℹ️ Info",
    "about_title": "ℹ️  About Spodo",
    "close": "Close",
    "theme_toggle_tip": "Toggle Light / Dark mode",

    # Input section
    "url_placeholder": "Paste a Spotify playlist, album, or track URL...",
    "paste_btn": "📋 Paste",
    "fetch_btn": "🔎 Fetch",
    "fetching": "⏳ Loading...",
    "my_playlists": "📋 My Playlists",
    "liked_songs": "❤️ Liked Songs",

    # Track list & Selection
    "filter_placeholder": "🔍 Filter tracks by title, artist, or album...",
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
    "retry_failed_btn": "🔁 Retry Failed ({count})",
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
    "concurrent_label": "Concurrent downloads:",
    "concurrent_sub": "1 = Safest against bot blocks, 2-3 = Faster parallel downloads.",
    "sec_cookies": "🍪 YouTube Cookies (Anti-Bot Bypass)",
    "sec_cookies_sub": "Optional. Prevents YouTube 'Sign in to confirm you’re not a bot' blocks.",
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
    "sec_ui": "Appearance",
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
        "Note: Most downloads work fine with Source set to 'none'.\n\n"
        "Option 1: cookies.txt File (Recommended on Windows)\n"
        "• Install the browser extension 'Get cookies.txt LOCALLY'.\n"
        "• Visit youtube.com (while signed in) and export your cookies.\n"
        "• Select 'file' as Source in Spodo and browse for your cookies.txt file.\n\n"
        "Option 2: Browser Cookies (Firefox / macOS / Linux)\n"
        "• Select your browser from the dropdown menu.\n"
        "• Click 'Sync' to cache your cookies locally.\n"
        "• Note: Modern Chrome/Brave on Windows uses App-Bound Encryption\n"
        "  (DPAPI), so use Option 1 (cookies.txt) or 'none' instead."
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
}


def get_language() -> str:
    """Return active language code ('en')."""
    return _CURRENT_LANGUAGE


def set_language(lang: str) -> None:
    """No-op: Spodo is English-only."""
    global _CURRENT_LANGUAGE
    _CURRENT_LANGUAGE = "en"


def t(key: str, **kwargs: Any) -> str:
    """Look up a UI string by key and format with kwargs if provided."""
    text = STRINGS.get(key, key)
    if kwargs:
        try:
            return text.format(**kwargs)
        except Exception:
            return text
    return text
