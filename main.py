"""
Spodo - Spotify Playlist Downloader
Hoofd-GUI gebouwd met CustomTkinter (dark mode).
Alle blokkerende taken draaien in daemon threads; UI-updates via app.after().
"""

import queue
import re
import threading
import tkinter as tk
from tkinter import filedialog
from typing import Optional

import customtkinter as ctk

from config import load_config, save_config
from downloader import (
    Downloader,
    ensure_ffmpeg,
    find_ffmpeg,
    test_youtube_auth,
    sync_browser_cookies,
    get_saved_cookie_count,
)
from spotify_client import SpotifyClient

from i18n import t, set_language, get_language

# ------------------------------------------------------------------
# Thema & Kleuren (Dynamisch Licht/Donker)
# ------------------------------------------------------------------
ctk.set_default_color_theme("blue")

SPOTIFY_GREEN = "#1DB954"
SPOTIFY_GREEN_HOVER = "#18a34a"

# Dynamische kleuren: tuple (Licht, Donker)
CARD_BG = ("#ffffff", "#1e293b")
ACCENT = ("#e2e8f0", "#334155")
ACCENT_HOVER = ("#cbd5e1", "#475569")
TEXT_PRIMARY = ("#0f172a", "#f8fafc")
TEXT_SECONDARY = ("#64748b", "#94a3b8")
LOG_BG = ("#ffffff", "#020617")
LOG_TEXT = ("#0f172a", "#c9d1d9")


def _format_duration(ms: int) -> str:
    """Formateer milliseconden naar m:ss."""
    total_sec = ms // 1000
    return f"{total_sec // 60}:{total_sec % 60:02d}"


# ══════════════════════════════════════════════════════════════════
# Instellingen-dialoog
# ══════════════════════════════════════════════════════════════════

class SettingsDialog(ctk.CTkToplevel):
    """Pop-up voor het bewerken van Spotify-credentials, output-, taal- en cookie-instellingen."""

    def __init__(self, parent, config: dict, on_save):
        super().__init__(parent)
        self.title(t("settings_title"))
        self.geometry("540x670")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self._config = config.copy()
        self._on_save = on_save

        # Scrollable container voor alle instellingen
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=8, pady=(8, 0))

        pad = {"padx": 16, "pady": (8, 2)}

        # --- SECTIE 1: SPOTIFY ---
        ctk.CTkLabel(scroll, text=t("sec_spotify"), font=ctk.CTkFont(size=14, weight="bold"), text_color=TEXT_PRIMARY).pack(anchor="w", padx=16, pady=(6, 2))
        ctk.CTkLabel(scroll, text=t("sec_spotify_sub"), font=ctk.CTkFont(size=11), text_color=TEXT_SECONDARY).pack(anchor="w", padx=16, pady=(0, 4))

        ctk.CTkLabel(scroll, text=t("client_id"), text_color=TEXT_PRIMARY).pack(anchor="w", **pad)
        self._id_entry = ctk.CTkEntry(scroll, width=470)
        self._id_entry.insert(0, config.get("client_id", ""))
        self._id_entry.pack(padx=16)

        ctk.CTkLabel(scroll, text=t("client_secret"), text_color=TEXT_PRIMARY).pack(anchor="w", **pad)
        self._secret_entry = ctk.CTkEntry(scroll, width=470, show="•")
        self._secret_entry.insert(0, config.get("client_secret", ""))
        self._secret_entry.pack(padx=16)

        ctk.CTkLabel(scroll, text=t("redirect_uri"), text_color=TEXT_PRIMARY).pack(anchor="w", **pad)
        self._uri_entry = ctk.CTkEntry(scroll, width=470)
        self._uri_entry.insert(0, config.get("redirect_uri", "http://127.0.0.1:3001/api/callback"))
        self._uri_entry.pack(padx=16)

        # --- SECTIE 2: AUDIO FORMAAT ---
        ctk.CTkLabel(scroll, text=t("sec_audio"), font=ctk.CTkFont(size=14, weight="bold"), text_color=TEXT_PRIMARY).pack(anchor="w", padx=16, pady=(16, 4))

        row_fmt = ctk.CTkFrame(scroll, fg_color="transparent")
        row_fmt.pack(fill="x", padx=16, pady=(4, 2))

        ctk.CTkLabel(row_fmt, text=t("format_label"), text_color=TEXT_PRIMARY).pack(side="left")
        self._format_var = ctk.StringVar(value=config.get("output_format", "mp3"))
        ctk.CTkOptionMenu(
            row_fmt, variable=self._format_var,
            values=["mp3", "flac", "ogg", "opus", "m4a", "wav"],
            width=100,
        ).pack(side="left", padx=(8, 24))

        ctk.CTkLabel(row_fmt, text=t("bitrate_label"), text_color=TEXT_PRIMARY).pack(side="left")
        self._bitrate_var = ctk.StringVar(value=config.get("bitrate", "320k"))
        ctk.CTkOptionMenu(
            row_fmt, variable=self._bitrate_var,
            values=["128k", "192k", "256k", "320k"],
            width=100,
        ).pack(side="left", padx=(8, 24))

        ctk.CTkLabel(row_fmt, text=t("concurrent_label"), text_color=TEXT_PRIMARY).pack(side="left")
        cur_concurrent = str(config.get("concurrent_downloads", 2))
        self._concurrent_var = ctk.StringVar(value=cur_concurrent)
        ctk.CTkOptionMenu(
            row_fmt, variable=self._concurrent_var,
            values=["1", "2", "3", "4"],
            width=70,
        ).pack(side="left", padx=8)

        ctk.CTkLabel(
            scroll,
            text=t("concurrent_sub"),
            font=ctk.CTkFont(size=11), text_color=TEXT_SECONDARY,
        ).pack(anchor="w", padx=16, pady=(0, 6))

        # --- SECTIE 3: YOUTUBE COOKIES / BOT BEVEILIGING ---
        ctk.CTkLabel(scroll, text=t("sec_cookies"), font=ctk.CTkFont(size=14, weight="bold"), text_color=TEXT_PRIMARY).pack(anchor="w", padx=16, pady=(16, 2))
        ctk.CTkLabel(
            scroll,
            text=t("sec_cookies_sub"),
            font=ctk.CTkFont(size=11), text_color=TEXT_SECONDARY
        ).pack(anchor="w", padx=16, pady=(0, 6))

        row_cookie = ctk.CTkFrame(scroll, fg_color="transparent")
        row_cookie.pack(fill="x", padx=16, pady=2)

        ctk.CTkLabel(row_cookie, text=t("cookie_source"), text_color=TEXT_PRIMARY).pack(side="left")
        self._cookie_var = ctk.StringVar(value=config.get("cookie_source", "none").lower())
        browser_choices = ["none", "brave", "chrome", "edge", "firefox", "opera", "vivaldi", "file"]
        self._cookie_menu = ctk.CTkOptionMenu(
            row_cookie, variable=self._cookie_var,
            values=browser_choices,
            command=self._on_cookie_source_change,
            width=120,
        )
        self._cookie_menu.pack(side="left", padx=(8, 12))

        ctk.CTkButton(
            row_cookie, text=t("cookie_help"), width=120, height=28,
            fg_color=ACCENT, hover_color=ACCENT_HOVER, font=ctk.CTkFont(size=11),
            text_color=TEXT_PRIMARY,
            command=self._open_cookie_help,
        ).pack(side="left")

        # Browser synchronisatie rij (zichtbaar als browser geselecteerd is)
        self._browser_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        self._sync_btn = ctk.CTkButton(
            self._browser_frame, text=t("sync_browser", browser=self._cookie_var.get().capitalize()),
            width=210, height=28, fg_color=ACCENT, hover_color=ACCENT_HOVER,
            text_color=TEXT_PRIMARY,
            command=self._sync_cookies,
        )
        self._sync_btn.pack(side="left", padx=(0, 10))
        self._sync_status = ctk.CTkLabel(
            self._browser_frame, text="", font=ctk.CTkFont(size=11), anchor="w",
        )
        self._sync_status.pack(side="left", fill="x", expand=True)

        # Bestandskeuze rij (zichtbaar als cookie_source == 'file')
        self._file_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        self._cookie_file_entry = ctk.CTkEntry(self._file_frame, width=340, placeholder_text=t("cookie_path_placeholder"))
        self._cookie_file_entry.insert(0, config.get("cookie_file", ""))
        self._cookie_file_entry.pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            self._file_frame, text=t("browse"), width=100, height=28,
            fg_color=ACCENT, hover_color=ACCENT_HOVER,
            text_color=TEXT_PRIMARY,
            command=self._browse_cookie_file,
        ).pack(side="left")

        # Test knop & resultaat
        row_test = ctk.CTkFrame(scroll, fg_color="transparent")
        row_test.pack(fill="x", padx=16, pady=(10, 4))

        self._test_btn = ctk.CTkButton(
            row_test, text=t("test_connection"), width=140, height=30,
            fg_color=ACCENT, hover_color=ACCENT_HOVER,
            text_color=TEXT_PRIMARY,
            command=self._test_cookies,
        )
        self._test_btn.pack(side="left")

        self._test_result_label = ctk.CTkLabel(
            row_test, text="", font=ctk.CTkFont(size=11), text_color=TEXT_SECONDARY, anchor="w",
        )
        self._test_result_label.pack(side="left", padx=10, fill="x", expand=True)

        self._update_cookie_view()

        # --- SECTIE 4: WEERGAVE & TAAL ---
        ctk.CTkLabel(scroll, text=t("sec_ui"), font=ctk.CTkFont(size=14, weight="bold"), text_color=TEXT_PRIMARY).pack(anchor="w", padx=16, pady=(16, 4))

        row_ui = ctk.CTkFrame(scroll, fg_color="transparent")
        row_ui.pack(fill="x", padx=16, pady=(4, 2))

        ctk.CTkLabel(row_ui, text=t("language_label"), text_color=TEXT_PRIMARY).pack(side="left")
        current_lang = config.get("language", "nl")
        self._lang_var = ctk.StringVar(value="Nederlands" if current_lang == "nl" else "English")
        self._lang_menu = ctk.CTkOptionMenu(
            row_ui, variable=self._lang_var,
            values=["Nederlands", "English"],
            width=130,
        )
        self._lang_menu.pack(side="left", padx=(8, 24))

        ctk.CTkLabel(row_ui, text=t("theme_label"), text_color=TEXT_PRIMARY).pack(side="left")
        current_mode = config.get("appearance_mode", "dark").lower()
        mode_map = {
            "dark": t("theme_dark"),
            "light": t("theme_light"),
            "system": t("theme_system"),
        }
        self._theme_var = ctk.StringVar(value=mode_map.get(current_mode, t("theme_dark")))
        self._theme_menu = ctk.CTkOptionMenu(
            row_ui, variable=self._theme_var,
            values=[t("theme_dark"), t("theme_light"), t("theme_system")],
            width=140,
        )
        self._theme_menu.pack(side="left", padx=8)

        # Opslaan knop onderaan
        ctk.CTkButton(
            self, text=t("save_settings"), fg_color=SPOTIFY_GREEN, hover_color=SPOTIFY_GREEN_HOVER,
            command=self._save, height=38, font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(pady=(8, 12))

    def _update_cookie_view(self):
        val = self._cookie_var.get()
        if val == "file":
            self._browser_frame.pack_forget()
            self._file_frame.pack(fill="x", padx=16, pady=(4, 2))
        elif val in ("brave", "chrome", "edge", "firefox", "opera", "safari", "vivaldi"):
            self._file_frame.pack_forget()
            self._sync_btn.configure(text=t("sync_browser", browser=val.capitalize()))
            count = get_saved_cookie_count()
            if count > 0:
                self._sync_status.configure(
                    text=t("sync_saved", count=count),
                    text_color=SPOTIFY_GREEN,
                )
            else:
                self._sync_status.configure(
                    text=t("sync_empty"),
                    text_color=TEXT_SECONDARY,
                )
            self._browser_frame.pack(fill="x", padx=16, pady=(4, 2))
        else:
            self._file_frame.pack_forget()
            self._browser_frame.pack_forget()

    def _on_cookie_source_change(self, val):
        self._update_cookie_view()

    def _sync_cookies(self):
        val = self._cookie_var.get()
        self._sync_btn.configure(state="disabled", text=t("syncing"))
        self._sync_status.configure(text=t("sync_fetching"), text_color=TEXT_SECONDARY)

        def worker():
            ok, msg, count = sync_browser_cookies(val)
            def update():
                self._sync_btn.configure(state="normal", text=t("sync_browser", browser=val.capitalize()))
                color = SPOTIFY_GREEN if ok else "#f39c12"
                self._sync_status.configure(text=msg, text_color=color)
            self.after(0, update)

        threading.Thread(target=worker, daemon=True).start()

    def _browse_cookie_file(self):
        filename = filedialog.askopenfilename(
            title=t("select_cookies_file"),
            filetypes=[("Text files / Tekstbestanden", "*.txt"), ("All files / Alle bestanden", "*.*")],
        )
        if filename:
            self._cookie_file_entry.delete(0, "end")
            self._cookie_file_entry.insert(0, filename)

    def _open_cookie_help(self):
        dlg = ctk.CTkToplevel(self)
        dlg.title(t("help_dialog_title"))
        dlg.geometry("540x440")
        dlg.resizable(False, False)
        dlg.transient(self)
        dlg.grab_set()

        ctk.CTkLabel(
            dlg, text=t("help_dialog_heading"),
            font=ctk.CTkFont(size=15, weight="bold"), text_color=SPOTIFY_GREEN,
        ).pack(anchor="w", padx=18, pady=(16, 8))

        ctk.CTkLabel(
            dlg, text=t("help_dialog_text"), justify="left", font=ctk.CTkFont(size=12),
            text_color=TEXT_PRIMARY,
        ).pack(anchor="w", padx=18, pady=4)

        ctk.CTkButton(
            dlg, text=t("understood"), width=110, height=32,
            fg_color=SPOTIFY_GREEN, hover_color=SPOTIFY_GREEN_HOVER,
            command=dlg.destroy,
        ).pack(pady=16)

    def _test_cookies(self):
        src = self._cookie_var.get()
        cf = self._cookie_file_entry.get().strip()
        self._test_btn.configure(state="disabled", text=t("testing_connection"))
        self._test_result_label.configure(text=t("checking_connection"), text_color=TEXT_SECONDARY)

        def worker():
            ok, msg = test_youtube_auth(src, cf)
            color = SPOTIFY_GREEN if ok else "#e74c3c"
            self.after(0, lambda: self._test_result_label.configure(text=msg, text_color=color))
            self.after(0, lambda: self._test_btn.configure(state="normal", text=t("test_connection")))

        threading.Thread(target=worker, daemon=True).start()

    def _save(self):
        self._config["client_id"] = self._id_entry.get().strip()
        self._config["client_secret"] = self._secret_entry.get().strip()
        self._config["redirect_uri"] = self._uri_entry.get().strip()
        self._config["output_format"] = self._format_var.get()
        self._config["bitrate"] = self._bitrate_var.get()
        try:
            self._config["concurrent_downloads"] = int(self._concurrent_var.get())
        except (ValueError, TypeError):
            self._config["concurrent_downloads"] = 2
        self._config["cookie_source"] = self._cookie_var.get()
        self._config["cookie_file"] = self._cookie_file_entry.get().strip()

        # Taal
        chosen_lang = "nl" if "Nederlands" in self._lang_var.get() else "en"
        self._config["language"] = chosen_lang
        set_language(chosen_lang)

        # Thema
        chosen_theme_str = self._theme_var.get()
        if "Licht" in chosen_theme_str or "Light" in chosen_theme_str:
            new_mode = "light"
        elif "Systeem" in chosen_theme_str or "System" in chosen_theme_str:
            new_mode = "system"
        else:
            new_mode = "dark"
        self._config["appearance_mode"] = new_mode
        ctk.set_appearance_mode(new_mode)

        save_config(self._config)
        self._on_save(self._config)
        self.destroy()


# ══════════════════════════════════════════════════════════════════
# Over Spodo / Vibe-Coded Disclaimer Dialoog
# ══════════════════════════════════════════════════════════════════

class AboutDialog(ctk.CTkToplevel):
    """Over Spodo / Info pop-up."""

    def __init__(self, parent):
        super().__init__(parent)
        self.title(t("about_title"))
        self.geometry("480x370")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        ctk.CTkLabel(
            self, text="🎵 Spodo",
            font=ctk.CTkFont(size=24, weight="bold"), text_color=SPOTIFY_GREEN,
        ).pack(pady=(22, 2))

        ctk.CTkLabel(
            self, text="Spotify Playlist & Track Downloader  •  v1.0.0",
            font=ctk.CTkFont(size=12), text_color=TEXT_SECONDARY,
        ).pack(pady=(0, 14))

        card = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=12)
        card.pack(fill="both", expand=True, padx=22, pady=(0, 16))

        info_msg = (
            "Spodo is een open-source muziekdownloader, gebouwd door Jente\n"
            "in samenwerking met Google Gemini.\n\n"
            "🧑‍💻 Jente (@jente509) — Projectbedenker (IT-student)\n"
            "🤖 Google Gemini — Code architectuur & ontwikkeling\n\n"
            "Gemaakt uit frustratie met haperende downloaders en bot-blokkades.\n"
            "Veel luisterplezier! 🎧"
            if get_language() == "nl" else
            "Spodo is an open-source Spotify downloader, built by Jente\n"
            "in collaboration with Google Gemini.\n\n"
            "🧑‍💻 Jente (@jente509) — Project Creator (IT Student)\n"
            "🤖 Google Gemini — Code Architecture & Development\n\n"
            "Built out of frustration with broken downloaders and bot blocks.\n"
            "Enjoy your music! 🎧"
        )

        ctk.CTkLabel(
            card, text=info_msg,
            font=ctk.CTkFont(size=12), justify="center", text_color=TEXT_PRIMARY,
        ).pack(padx=16, pady=24)

        ctk.CTkButton(
            self, text=t("close"), width=120, height=32,
            fg_color=SPOTIFY_GREEN, hover_color=SPOTIFY_GREEN_HOVER,
            command=self.destroy,
        ).pack(pady=(0, 18))


# ══════════════════════════════════════════════════════════════════
# Playlist-kiezer dialoog
# ══════════════════════════════════════════════════════════════════

class PlaylistPickerDialog(ctk.CTkToplevel):
    """Pop-up die de playlists van de gebruiker toont om er één te selecteren."""

    def __init__(self, parent, playlists: list[dict], on_select):
        super().__init__(parent)
        self.title(t("choose_playlist_title"))
        self.geometry("600x520")
        self.transient(parent)
        self.grab_set()

        self._on_select = on_select

        ctk.CTkLabel(
            self, text=t("choose_playlist_heading"),
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=TEXT_PRIMARY,
        ).pack(pady=(14, 6))

        scroll = ctk.CTkScrollableFrame(self, width=560, height=420)
        scroll.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        for pl in playlists:
            frame = ctk.CTkFrame(scroll, fg_color=CARD_BG, corner_radius=8)
            frame.pack(fill="x", pady=3, padx=4)

            info_frame = ctk.CTkFrame(frame, fg_color="transparent")
            info_frame.pack(side="left", fill="x", expand=True, padx=10, pady=6)

            ctk.CTkLabel(
                info_frame, text=pl["name"],
                font=ctk.CTkFont(size=13, weight="bold"), anchor="w",
                text_color=TEXT_PRIMARY,
            ).pack(anchor="w")
            num_suffix = "nummers" if get_language() == "nl" else "tracks"
            ctk.CTkLabel(
                info_frame,
                text=f"{pl['owner']}  •  {pl['tracks_total']} {num_suffix}",
                font=ctk.CTkFont(size=11), text_color=TEXT_SECONDARY, anchor="w",
            ).pack(anchor="w")

            btn_txt = "Laden" if get_language() == "nl" else "Load"
            ctk.CTkButton(
                frame, text=btn_txt, width=70, height=28,
                fg_color=SPOTIFY_GREEN, hover_color=SPOTIFY_GREEN_HOVER,
                command=lambda p=pl: self._pick(p),
            ).pack(side="right", padx=10, pady=6)

    def _pick(self, playlist: dict):
        self._on_select(playlist)
        self.destroy()


# ══════════════════════════════════════════════════════════════════
# Track-rij widget
# ══════════════════════════════════════════════════════════════════

class TrackRow(ctk.CTkFrame):
    """Eén rij in de tracklist met checkbox, naam, album en duur."""

    def __init__(self, parent, index: int, track: dict, **kwargs):
        super().__init__(parent, fg_color="transparent", height=32, **kwargs)
        self.track = track
        self.var = ctk.BooleanVar(value=True)

        self.grid_columnconfigure(1, weight=3)
        self.grid_columnconfigure(2, weight=2)

        self.cb = ctk.CTkCheckBox(
            self, variable=self.var, text="",
            width=24, checkbox_width=20, checkbox_height=20,
            fg_color=SPOTIFY_GREEN, hover_color=SPOTIFY_GREEN_HOVER,
        )
        self.cb.grid(row=0, column=0, padx=(4, 2), sticky="w")

        title_text = f"{index}. {track['artists']} — {track['name']}"
        ctk.CTkLabel(
            self, text=title_text,
            font=ctk.CTkFont(size=12), anchor="w",
            text_color=TEXT_PRIMARY,
        ).grid(row=0, column=1, padx=4, sticky="w")

        ctk.CTkLabel(
            self, text=track.get("album", ""),
            font=ctk.CTkFont(size=11), text_color=TEXT_SECONDARY, anchor="w",
        ).grid(row=0, column=2, padx=4, sticky="w")

        ctk.CTkLabel(
            self, text=_format_duration(track.get("duration_ms", 0)),
            font=ctk.CTkFont(size=11), text_color=TEXT_SECONDARY, width=45, anchor="e",
        ).grid(row=0, column=3, padx=(4, 8), sticky="e")


# ══════════════════════════════════════════════════════════════════
# Hoofd-applicatie
# ══════════════════════════════════════════════════════════════════

class SpodoApp(ctk.CTk):
    """Spodo hoofdvenster."""

    def __init__(self):
        super().__init__()
        self.title(t("app_title"))
        self.geometry("1050x760")
        self.minsize(800, 600)

        # State
        self.cfg = load_config()
        # Activeer taal en appearance mode uit config
        set_language(self.cfg.get("language", "nl"))
        ctk.set_appearance_mode(self.cfg.get("appearance_mode", "dark"))
        self.sp_client: Optional[SpotifyClient] = None
        self.track_rows: list[TrackRow] = []
        self.current_tracks: list[dict] = []
        self.collection_name: str = ""
        self.downloader: Optional[Downloader] = None
        self._downloading = False
        self._tracks_loaded = False   # True zodra een fetch is uitgevoerd (ook als leeg)

        # Thread-safe queue voor UI updates vanuit achtergrondthreads
        self._ui_queue = queue.Queue()
        self._process_ui_queue()

        # Init Spotify client
        self._init_spotify_client()

        # Bouw UI
        self._build_top_bar()
        self._build_input_section()
        self._build_track_list()
        self._build_bottom_bar()

        # Probeer bestaande sessie te herstellen + check ffmpeg (in achtergrond)
        threading.Thread(target=self._startup_checks, daemon=True).start()

        # Netjes afsluiten
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ------------------------------------------------------------------
    # Thread-safe UI communicatie
    # ------------------------------------------------------------------

    def ui_call(self, func, *args, **kwargs):
        """Thread-safe aanroep van een UI-functie vanuit een achtergrondthread."""
        self._ui_queue.put((func, args, kwargs))

    def _process_ui_queue(self):
        """Draait op de main thread en voert callbacks uit de queue uit."""
        try:
            while True:
                func, args, kwargs = self._ui_queue.get_nowait()
                try:
                    func(*args, **kwargs)
                except Exception:
                    pass
        except queue.Empty:
            pass
        self.after(30, self._process_ui_queue)

    # ------------------------------------------------------------------
    # Initialisatie
    # ------------------------------------------------------------------

    def _init_spotify_client(self):
        self.sp_client = SpotifyClient(
            client_id=self.cfg.get("client_id", ""),
            client_secret=self.cfg.get("client_secret", ""),
            redirect_uri=self.cfg.get("redirect_uri", "http://127.0.0.1:3001/api/callback"),
        )

    def _startup_checks(self):
        """Achtergrond-checks bij het opstarten."""
        # Sessie herstellen
        try:
            if self.sp_client.try_restore_session():
                self.ui_call(self._refresh_login_ui)
                self.ui_call(self._log, t("session_restored", name=self.sp_client.get_display_name()))
        except Exception:
            pass

        # FFmpeg check — als het niet bestaat, blokkeer de download-knop tijdens installatie
        self.ui_call(self._log, t("check_ffmpeg"))
        ffmpeg_needs_download = not find_ffmpeg()
        if ffmpeg_needs_download:
            self.ui_call(self._set_ffmpeg_downloading, True)

        ok = ensure_ffmpeg(on_log=lambda msg: self.ui_call(self._log, msg))

        if ffmpeg_needs_download:
            self.ui_call(self._set_ffmpeg_downloading, False)

        if ok:
            self.ui_call(self._log, t("ffmpeg_available"))
        else:
            self.ui_call(self._log, t("ffmpeg_missing"))

        # Muziekmap check
        if not self.cfg.get("music_dir"):
            self.ui_call(self._log, t("music_dir_missing"))

        # YouTube Cookie check
        cookie_src = (self.cfg.get("cookie_source") or "none").lower()
        if cookie_src == "file":
            cf = self.cfg.get("cookie_file", "")
            if cf and Path(cf).exists():
                count = get_saved_cookie_count(Path(cf))
                self.ui_call(self._log, t("cookies_loaded_file", name=Path(cf).name, count=count))
            else:
                self.ui_call(self._log, t("cookies_file_missing"))
        elif cookie_src in ("brave", "chrome", "edge", "firefox", "opera", "safari", "vivaldi"):
            count = get_saved_cookie_count()
            if count > 0:
                self.ui_call(self._log, t("cookies_active_browser", count=count, browser=cookie_src.capitalize()))
            else:
                self.ui_call(self._log, t("cookies_active_browser_none", browser=cookie_src.capitalize()))

    def _set_ffmpeg_downloading(self, downloading: bool):
        """Schakel de download-knop in/uit tijdens FFmpeg-installatie."""
        if downloading:
            self._download_btn.configure(
                state="disabled",
                text=t("ffmpeg_downloading"),
            )
            self._log(t("ffmpeg_downloading"))
        else:
            # Herstel de knop — alleen inschakelen als er tracks geselecteerd zijn
            if self.current_tracks:
                self._download_btn.configure(state="normal", text=t("download_btn"))
            else:
                self._download_btn.configure(state="disabled", text=t("download_btn"))



    # ------------------------------------------------------------------
    # UI opbouw
    # ------------------------------------------------------------------

    def _build_top_bar(self):
        top = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=0)
        top.pack(fill="x", padx=0, pady=0)

        # Rij 1: Branding + actieknoppen
        row1 = ctk.CTkFrame(top, fg_color="transparent")
        row1.pack(fill="x", padx=16, pady=(10, 4))

        brand_frame = ctk.CTkFrame(row1, fg_color="transparent")
        brand_frame.pack(side="left")

        ctk.CTkLabel(
            brand_frame, text="🎵 Spodo",
            font=ctk.CTkFont(size=22, weight="bold"), text_color=SPOTIFY_GREEN,
        ).pack(side="left")

        self._info_btn = ctk.CTkButton(
            brand_frame, text=t("info_btn"), width=65, height=24,
            fg_color=CARD_BG, hover_color=ACCENT,
            text_color=TEXT_SECONDARY,
            font=ctk.CTkFont(size=11, weight="bold"),
            corner_radius=12,
            command=self._open_about,
        )
        self._info_btn.pack(side="left", padx=(10, 0))

        # Rechter knoppen
        btn_frame = ctk.CTkFrame(row1, fg_color="transparent")
        btn_frame.pack(side="right")

        # Instellingen knop
        self._settings_btn = ctk.CTkButton(
            btn_frame, text="⚙", width=36, height=32,
            fg_color="transparent", hover_color=ACCENT,
            command=self._open_settings,
        )
        self._settings_btn.pack(side="right", padx=(2, 0))

        # Thema toggle (Licht / Donker)
        cur_mode = ctk.get_appearance_mode().lower()
        theme_icon = "☀️" if cur_mode == "light" else "🌙"
        self._theme_btn = ctk.CTkButton(
            btn_frame, text=theme_icon, width=36, height=32,
            fg_color="transparent", hover_color=ACCENT,
            font=ctk.CTkFont(size=14),
            command=self._toggle_theme,
        )
        self._theme_btn.pack(side="right", padx=2)

        # Taal toggle (NL / EN)
        lang_text = "🇬🇧 EN" if get_language() == "nl" else "🇳🇱 NL"
        self._lang_btn = ctk.CTkButton(
            btn_frame, text=lang_text, width=64, height=32,
            fg_color="transparent", hover_color=ACCENT,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._toggle_language,
        )
        self._lang_btn.pack(side="right", padx=2)

        self._logout_btn = ctk.CTkButton(
            btn_frame, text=t("logout"), width=80, height=32,
            fg_color="transparent", hover_color=ACCENT, text_color=TEXT_SECONDARY,
            command=self._logout_spotify,
        )
        # Wordt pas gepacked als ingelogd

        self._login_btn = ctk.CTkButton(
            btn_frame, text=t("login_spotify"), width=190, height=32,
            fg_color=SPOTIFY_GREEN, hover_color=SPOTIFY_GREEN_HOVER,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._login_spotify,
        )
        self._login_btn.pack(side="right", padx=4)

        self._login_status_label = ctk.CTkLabel(
            btn_frame, text=t("public_mode"),
            font=ctk.CTkFont(size=12), text_color=TEXT_SECONDARY,
        )
        self._login_status_label.pack(side="right", padx=(0, 10))

        # Rij 2: Muziekmap & Cookies
        row2 = ctk.CTkFrame(top, fg_color="transparent")
        row2.pack(fill="x", padx=16, pady=(0, 10))

        self._dir_title_label = ctk.CTkLabel(row2, text=t("download_dir"), font=ctk.CTkFont(size=12), text_color=TEXT_PRIMARY)
        self._dir_title_label.pack(side="left")

        self._dir_label = ctk.CTkLabel(
            row2,
            text=self.cfg.get("music_dir") or t("not_set"),
            font=ctk.CTkFont(size=12), text_color=SPOTIFY_GREEN,
        )
        self._dir_label.pack(side="left", padx=(6, 0))

        self._change_dir_btn = ctk.CTkButton(
            row2, text=t("change_dir"), width=90, height=28,
            fg_color=ACCENT, hover_color=ACCENT_HOVER, text_color=TEXT_PRIMARY,
            command=self._change_music_dir,
        )
        self._change_dir_btn.pack(side="left", padx=10)

        self._cookie_btn = ctk.CTkButton(
            row2, text=self._get_cookie_btn_text(), width=160, height=28,
            fg_color=ACCENT, hover_color=ACCENT_HOVER, text_color=TEXT_PRIMARY,
            command=self._open_settings,
        )
        self._cookie_btn.pack(side="right")

    def _get_cookie_btn_text(self) -> str:
        from pathlib import Path
        src = (self.cfg.get("cookie_source") or "none").lower()
        if src == "file":
            cf = self.cfg.get("cookie_file", "")
            name = Path(cf).name if cf else "cookies.txt"
            return t("cookies_file", name=name)
        elif src and src != "none":
            count = get_saved_cookie_count()
            if count > 0:
                return t("cookies_browser", source=src.capitalize(), count=count)
            return t("cookies_browser_nocount", source=src.capitalize())
        return t("cookies_none")

    def _toggle_theme(self):
        """Wissel direct tussen Dark en Light mode."""
        cur = ctk.get_appearance_mode().lower()
        new_mode = "light" if cur == "dark" else "dark"
        ctk.set_appearance_mode(new_mode)
        self.cfg["appearance_mode"] = new_mode
        save_config(self.cfg)
        self._theme_btn.configure(text="☀️" if new_mode == "light" else "🌙")

    def _toggle_language(self):
        """Wissel direct tussen Nederlands en Engels."""
        new_lang = "en" if get_language() == "nl" else "nl"
        set_language(new_lang)
        self.cfg["language"] = new_lang
        save_config(self.cfg)
        self._apply_translations()

    def _apply_translations(self):
        """Werk alle zichtbare UI-elementen bij naar de geselecteerde taal."""
        self.title(t("app_title"))
        self._info_btn.configure(text=t("info_btn"))
        self._lang_btn.configure(text="🇬🇧 EN" if get_language() == "nl" else "🇳🇱 NL")
        self._logout_btn.configure(text=t("logout"))
        if not (self.sp_client and self.sp_client.is_logged_in()):
            self._login_btn.configure(text=t("login_spotify"))
            self._login_status_label.configure(text=t("public_mode"))
        else:
            self._login_status_label.configure(text=t("logged_in_as", name=self.sp_client.get_display_name()))

        self._dir_title_label.configure(text=t("download_dir"))
        if not self.cfg.get("music_dir"):
            self._dir_label.configure(text=t("not_set"))
        self._change_dir_btn.configure(text=t("change_dir"))
        self._cookie_btn.configure(text=self._get_cookie_btn_text())

        self._url_entry.configure(placeholder_text=t("url_placeholder"))
        self._fetch_btn.configure(text=t("fetch_btn"))
        self._playlists_btn.configure(text=t("my_playlists"))
        self._liked_btn.configure(text=t("liked_songs"))

        self._select_all_btn.configure(text=t("select_all"))
        self._deselect_all_btn.configure(text=t("deselect_all"))

        if not self.current_tracks:
            if self._tracks_loaded:
                # Fetch is uitgevoerd maar leverde niks op
                no_results = "Geen nummers gevonden." if get_language() == "nl" else "No tracks found."
                self._empty_label.configure(text=no_results)
            else:
                # Initiële staat: nog niks opgehaald
                self._empty_label.configure(text=t("empty_hint"))
        else:
            num_suffix = "nummers" if get_language() == "nl" else "tracks"
            self._track_count_label.configure(text=f"({len(self.current_tracks)} {num_suffix})")

        if not self._downloading:
            self._download_btn.configure(text=t("download_btn"))
        self._stop_btn.configure(text=t("stop_btn"))
        self._clear_log_btn.configure(text=t("clear_log"))

    def _clear_log(self):
        """Wis de inhoud van het log-venster."""
        self._log_box.configure(state="normal")
        self._log_box.delete("1.0", "end")
        self._log_box.configure(state="disabled")

    def _build_input_section(self):
        section = ctk.CTkFrame(self, fg_color="transparent")
        section.pack(fill="x", padx=16, pady=(12, 4))

        # URL invoer
        url_frame = ctk.CTkFrame(section, fg_color="transparent")
        url_frame.pack(fill="x")
        url_frame.grid_columnconfigure(0, weight=1)

        self._url_entry = ctk.CTkEntry(
            url_frame,
            placeholder_text=t("url_placeholder"),
            height=38, font=ctk.CTkFont(size=13),
        )
        self._url_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self._url_entry.bind("<Return>", lambda e: self._fetch_url())

        self._fetch_btn = ctk.CTkButton(
            url_frame, text=t("fetch_btn"), width=110, height=38,
            fg_color=SPOTIFY_GREEN, hover_color=SPOTIFY_GREEN_HOVER,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._fetch_url,
        )
        self._fetch_btn.grid(row=0, column=1)

        # Extra knoppen (ingelogd)
        self._extra_btns = ctk.CTkFrame(section, fg_color="transparent")
        self._extra_btns.pack(fill="x", pady=(6, 0))

        self._playlists_btn = ctk.CTkButton(
            self._extra_btns, text=t("my_playlists"), width=150, height=32,
            fg_color=ACCENT, hover_color=ACCENT_HOVER, text_color=TEXT_PRIMARY,
            command=self._load_my_playlists, state="disabled",
        )
        self._playlists_btn.pack(side="left", padx=(0, 8))

        self._liked_btn = ctk.CTkButton(
            self._extra_btns, text=t("liked_songs"), width=140, height=32,
            fg_color=ACCENT, hover_color=ACCENT_HOVER, text_color=TEXT_PRIMARY,
            command=self._load_liked_songs, state="disabled",
        )
        self._liked_btn.pack(side="left")

    def _build_track_list(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=(8, 2))

        self._collection_label = ctk.CTkLabel(
            header, text="", font=ctk.CTkFont(size=14, weight="bold"),
            text_color=TEXT_PRIMARY,
        )
        self._collection_label.pack(side="left")

        self._track_count_label = ctk.CTkLabel(
            header, text="", font=ctk.CTkFont(size=12), text_color=TEXT_SECONDARY,
        )
        self._track_count_label.pack(side="left", padx=8)

        sel_frame = ctk.CTkFrame(header, fg_color="transparent")
        sel_frame.pack(side="right")

        self._select_all_btn = ctk.CTkButton(
            sel_frame, text=t("select_all"), width=70, height=26,
            fg_color=ACCENT, hover_color=ACCENT_HOVER, text_color=TEXT_PRIMARY, font=ctk.CTkFont(size=11),
            command=self._select_all,
        )
        self._select_all_btn.pack(side="left", padx=2)

        self._deselect_all_btn = ctk.CTkButton(
            sel_frame, text=t("deselect_all"), width=70, height=26,
            fg_color=ACCENT, hover_color=ACCENT_HOVER, text_color=TEXT_PRIMARY, font=ctk.CTkFont(size=11),
            command=self._deselect_all,
        )
        self._deselect_all_btn.pack(side="left", padx=2)

        # Scrollable track lijst
        self._track_scroll = ctk.CTkScrollableFrame(
            self, fg_color=CARD_BG, corner_radius=10,
        )
        self._track_scroll.pack(fill="both", expand=True, padx=16, pady=(2, 4))
        self._track_scroll.grid_columnconfigure(0, weight=1)

        self._empty_box = ctk.CTkFrame(self._track_scroll, fg_color="transparent")
        self._empty_box.pack(pady=45)
        ctk.CTkLabel(self._empty_box, text="🎧", font=ctk.CTkFont(size=38)).pack()
        self._empty_label = ctk.CTkLabel(
            self._empty_box,
            text=t("empty_hint"),
            font=ctk.CTkFont(size=13), text_color=TEXT_SECONDARY, justify="center",
        )
        self._empty_label.pack(pady=(8, 0))

    def _build_bottom_bar(self):
        bottom = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=0)
        bottom.pack(fill="x", side="bottom", padx=0, pady=0)

        # Rij 1: Knoppen + voortgang
        row1 = ctk.CTkFrame(bottom, fg_color="transparent")
        row1.pack(fill="x", padx=16, pady=(10, 4))

        self._download_btn = ctk.CTkButton(
            row1, text=t("download_btn"), width=160, height=38,
            fg_color=SPOTIFY_GREEN, hover_color=SPOTIFY_GREEN_HOVER,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._start_download, state="disabled",
        )
        self._download_btn.pack(side="left")

        self._stop_btn = ctk.CTkButton(
            row1, text=t("stop_btn"), width=80, height=38,
            fg_color="#c0392b", hover_color="#e74c3c",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._stop_download, state="disabled",
        )
        self._stop_btn.pack(side="left", padx=10)

        self._clear_log_btn = ctk.CTkButton(
            row1, text=t("clear_log"), width=76, height=28,
            fg_color="transparent", hover_color=ACCENT, text_color=TEXT_SECONDARY,
            font=ctk.CTkFont(size=11),
            command=self._clear_log,
        )
        self._clear_log_btn.pack(side="left", padx=4)

        self._progress_label = ctk.CTkLabel(
            row1, text="", font=ctk.CTkFont(size=12), text_color=TEXT_PRIMARY,
        )
        self._progress_label.pack(side="right", padx=8)

        self._progress_bar = ctk.CTkProgressBar(row1, width=280, height=14)
        self._progress_bar.pack(side="right", padx=4)
        self._progress_bar.set(0)

        # Rij 2: Log
        self._log_box = ctk.CTkTextbox(
            bottom, height=110, font=ctk.CTkFont(family="Consolas", size=11),
            fg_color=LOG_BG, text_color=LOG_TEXT,
            state="disabled", wrap="word",
        )
        self._log_box.pack(fill="x", padx=16, pady=(0, 10))

    # ------------------------------------------------------------------
    # Login / Logout
    # ------------------------------------------------------------------

    def _login_spotify(self):
        self._login_btn.configure(state="disabled", text=t("fetching"))
        self._log("🔑 Spotify OAuth...")
        threading.Thread(target=self._login_worker, daemon=True).start()

    def _login_worker(self):
        try:
            self.sp_client.login_oauth()
            self.ui_call(self._refresh_login_ui)
            name = self.sp_client.get_display_name()
            self.ui_call(self._log, t("login_ok", name=name))
        except Exception as exc:
            self.ui_call(self._log, f"❌ Login error: {exc}")
            self.ui_call(lambda: self._login_btn.configure(state="normal", text=t("login_spotify")))

    def _logout_spotify(self):
        self.sp_client.logout()
        self._refresh_login_ui()
        self._log(t("public_mode"))

    def _refresh_login_ui(self):
        if self.sp_client.is_logged_in():
            name = self.sp_client.get_display_name()
            self._login_status_label.configure(text=t("logged_in_as", name=name), text_color=SPOTIFY_GREEN)
            self._login_btn.pack_forget()
            self._logout_btn.pack(side="right", padx=4)
            self._playlists_btn.configure(state="normal")
            self._liked_btn.configure(state="normal")
        else:
            self._login_status_label.configure(text=t("public_mode"), text_color=TEXT_SECONDARY)
            self._logout_btn.pack_forget()
            self._login_btn.configure(state="normal", text=t("login_spotify"))
            self._login_btn.pack(side="right", padx=4)
            self._playlists_btn.configure(state="disabled")
            self._liked_btn.configure(state="disabled")

    # ------------------------------------------------------------------
    # Muziekmap
    # ------------------------------------------------------------------

    def _change_music_dir(self):
        title = "Kies downloadmap" if get_language() == "nl" else "Choose download folder"
        new_dir = filedialog.askdirectory(
            title=title,
            initialdir=self.cfg.get("music_dir") or str(__import__("pathlib").Path.home()),
        )
        if new_dir:
            self.cfg["music_dir"] = new_dir
            save_config(self.cfg)
            self._dir_label.configure(text=new_dir)
            msg = f"📁 Downloadmap gewijzigd naar: {new_dir}" if get_language() == "nl" else f"📁 Download folder changed to: {new_dir}"
            self._log(msg)

    # ------------------------------------------------------------------
    # Instellingen
    # ------------------------------------------------------------------

    def _open_settings(self):
        SettingsDialog(self, self.cfg, self._on_settings_saved)

    def _open_about(self):
        AboutDialog(self)

    def _on_settings_saved(self, new_cfg: dict):
        self.cfg = new_cfg
        self._apply_translations()
        self._init_spotify_client()
        self._refresh_login_ui()
        if hasattr(self, "_cookie_btn"):
            self._cookie_btn.configure(text=self._get_cookie_btn_text())
        self._log(t("settings_saved_log"))

    # ------------------------------------------------------------------
    # URL ophalen
    # ------------------------------------------------------------------

    def _fetch_url(self):
        url = self._url_entry.get().strip()
        if not url:
            self._log(t("enter_url_warn"))
            return
        self._fetch_btn.configure(state="disabled", text=t("fetching"))
        self._log(t("fetching_url_log", url=url))
        threading.Thread(target=self._fetch_worker, args=(url,), daemon=True).start()

    def _fetch_worker(self, url: str):
        try:
            name, tracks = self.sp_client.fetch_from_url(url)
            self.ui_call(self._populate_tracks, name, tracks)
            self.ui_call(self._log, t("tracks_loaded_log", count=len(tracks), name=name))
        except Exception as exc:
            self.ui_call(self._log, t("fetch_error_log", error=exc))
        finally:
            self.ui_call(lambda: self._fetch_btn.configure(state="normal", text=t("fetch_btn")))

    # ------------------------------------------------------------------
    # Mijn Playlists / Liked Songs
    # ------------------------------------------------------------------

    def _load_my_playlists(self):
        self._playlists_btn.configure(state="disabled", text=t("fetching"))
        self._log(t("loading_playlists_log"))
        threading.Thread(target=self._playlists_worker, daemon=True).start()

    def _playlists_worker(self):
        try:
            playlists = self.sp_client.get_user_playlists()
            self.ui_call(self._show_playlist_picker, playlists)
            self.ui_call(self._log, t("playlists_found_log", count=len(playlists)))
        except Exception as exc:
            self.ui_call(self._log, t("playlist_error_log", error=exc))
        finally:
            self.ui_call(lambda: self._playlists_btn.configure(state="normal", text=t("my_playlists")))

    def _show_playlist_picker(self, playlists: list[dict]):
        if not playlists:
            self._log("ℹ️ " + ("Geen playlists gevonden." if get_language() == "nl" else "No playlists found."))
            return
        PlaylistPickerDialog(self, playlists, self._on_playlist_picked)

    def _on_playlist_picked(self, playlist: dict):
        url = playlist.get("url", "")
        if url:
            self._url_entry.delete(0, "end")
            self._url_entry.insert(0, url)
            self._fetch_url()

    def _load_liked_songs(self):
        self._liked_btn.configure(state="disabled", text=t("fetching"))
        self._log("❤️ Liked Songs...")
        threading.Thread(target=self._liked_worker, daemon=True).start()

    def _liked_worker(self):
        try:
            name, tracks = self.sp_client.get_liked_songs()
            self.ui_call(self._populate_tracks, name, tracks)
            msg = f"✅ {len(tracks)} Liked Songs geladen." if get_language() == "nl" else f"✅ Loaded {len(tracks)} Liked Songs."
            self.ui_call(self._log, msg)
        except Exception as exc:
            self.ui_call(self._log, t("playlist_error_log", error=exc))
        finally:
            self.ui_call(lambda: self._liked_btn.configure(state="normal", text=t("liked_songs")))

    # ------------------------------------------------------------------
    # Tracklist vullen
    # ------------------------------------------------------------------

    def _populate_tracks(self, name: str, tracks: list[dict]):
        self.collection_name = name
        self.current_tracks = tracks
        self._tracks_loaded = True

        # Verwijder alleen TrackRow-widgets (laat _empty_box intact)
        for row in self.track_rows:
            row.pack_forget()
            row.destroy()
        self.track_rows.clear()

        if not tracks:
            # Toon de lege-staat met "geen nummers gevonden"-tekst
            no_results = "Geen nummers gevonden." if get_language() == "nl" else "No tracks found."
            self._empty_label.configure(text=no_results)
            self._empty_box.pack(pady=45)
            self._download_btn.configure(state="disabled")
            self._collection_label.configure(text="")
            self._track_count_label.configure(text="")
            return

        # Verberg de lege staat
        self._empty_box.pack_forget()

        self._collection_label.configure(text=f"🎶 {name}")
        num_suffix = "nummers" if get_language() == "nl" else "tracks"
        self._track_count_label.configure(text=f"({len(tracks)} {num_suffix})")

        # Chunked / batch rendering zodat grote playlists (500 - 3000 nummers)
        # de gebruikersinterface niet laten bevriezen.
        chunk_size = 35

        def _render_chunk(start_idx: int):
            # Controleer of de tracks ondertussen niet vervangen zijn
            if self.current_tracks is not tracks:
                return

            end_idx = min(start_idx + chunk_size, len(tracks))
            for i in range(start_idx, end_idx):
                trk = tracks[i]
                row = TrackRow(self._track_scroll, index=i + 1, track=trk)
                row.pack(fill="x", pady=1)
                self.track_rows.append(row)

            if end_idx < len(tracks):
                self.after(5, _render_chunk, end_idx)
            else:
                self._download_btn.configure(state="normal")

        # Start de eerste batch direct en schakel downloadknop alvast in
        self._download_btn.configure(state="normal")
        _render_chunk(0)

    # ------------------------------------------------------------------
    # Selectie
    # ------------------------------------------------------------------

    def _select_all(self):
        for row in self.track_rows:
            row.var.set(True)

    def _deselect_all(self):
        for row in self.track_rows:
            row.var.set(False)

    # ------------------------------------------------------------------
    # Download
    # ------------------------------------------------------------------

    def _start_download(self):
        # Muziekmap controleren
        if not self.cfg.get("music_dir"):
            warn = "⚠️ Stel eerst een downloadmap in via 'Wijzig map'." if get_language() == "nl" else "⚠️ Please select a download folder first via 'Change folder'."
            self._log(warn)
            self._change_music_dir()
            if not self.cfg.get("music_dir"):
                return

        # Geselecteerde tracks verzamelen
        selected = [row.track for row in self.track_rows if row.var.get()]
        if not selected:
            warn = "⚠️ Selecteer minstens één nummer om te downloaden." if get_language() == "nl" else "⚠️ Please select at least one track to download."
            self._log(warn)
            return

        self._downloading = True
        self._download_btn.configure(state="disabled")
        self._stop_btn.configure(state="normal")
        self._fetch_btn.configure(state="disabled")
        self._progress_bar.set(0)
        progress_txt = f"0 / {len(selected)} " + ("gedownload" if get_language() == "nl" else "downloaded")
        self._progress_label.configure(text=progress_txt)
        self._log(t("download_started_log", count=len(selected), name=self.collection_name))

        self.downloader = Downloader(
            music_dir=self.cfg["music_dir"],
            output_format=self.cfg.get("output_format", "mp3"),
            bitrate=self.cfg.get("bitrate", "320k"),
            cookie_source=self.cfg.get("cookie_source", "none"),
            cookie_file=self.cfg.get("cookie_file", ""),
            concurrent_workers=self.cfg.get("concurrent_downloads", 2),
        )

        threading.Thread(
            target=self._download_worker,
            args=(selected, self.collection_name),
            daemon=True,
        ).start()

    def _download_worker(self, tracks: list[dict], name: str):
        self.downloader.download_tracks(
            tracks=tracks,
            collection_name=name,
            on_progress=lambda c, f, t: self.ui_call(self._update_progress, c, f, t),
            on_log=lambda msg: self.ui_call(self._log, msg),
            on_complete=lambda c, f, t: self.ui_call(self._on_download_complete, c, f, t),
        )

    def _stop_download(self):
        if self.downloader:
            self.downloader.cancel()
            self._log(t("stopping"))

    def _update_progress(self, completed: int, failed: int, total: int):
        fraction = (completed + failed) / total if total else 0
        self._progress_bar.set(fraction)
        dl_word = "gedownload" if get_language() == "nl" else "downloaded"
        fail_word = "mislukt" if get_language() == "nl" else "failed"
        self._progress_label.configure(text=f"{completed} / {total} {dl_word}" + (f" ({failed} {fail_word})" if failed else ""))

    def _on_download_complete(self, completed: int, failed: int, total: int):
        self._downloading = False
        self._download_btn.configure(state="normal")
        self._stop_btn.configure(state="disabled")
        self._fetch_btn.configure(state="normal")
        self._progress_bar.set(1.0 if not failed else (completed / total if total else 0))

    # ------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------

    def _log(self, message: str):
        cleaned = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', str(message))
        self._log_box.configure(state="normal")
        self._log_box.insert("end", cleaned + "\n")
        self._log_box.see("end")
        self._log_box.configure(state="disabled")

    # ------------------------------------------------------------------
    # Afsluiten
    # ------------------------------------------------------------------

    def _on_close(self):
        if self._downloading and self.downloader:
            self.downloader.cancel()
        self.destroy()


# ══════════════════════════════════════════════════════════════════
# Entrypoint
# ══════════════════════════════════════════════════════════════════

# Achterwaartse compatibiliteit
SpootyApp = SpodoApp


def main():
    app = SpodoApp()
    app.mainloop()


if __name__ == "__main__":
    main()
