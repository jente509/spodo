"""
Spodo - Spotify Client
Beheert authenticatie (public + OAuth) en metadata-ophalen via de Spotify Web API.
"""

import re
from typing import Optional

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth

from config import SPOTIFY_CACHE_PATH


class SpotifyClient:
    """Wrapper rond spotipy die zowel publieke als OAuth-modus ondersteunt."""

    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.sp: Optional[spotipy.Spotify] = None
        self.user_info: Optional[dict] = None
        self._init_public()

    # ------------------------------------------------------------------
    # Authenticatie
    # ------------------------------------------------------------------

    def _init_public(self) -> None:
        """Initialiseer in publieke modus (ClientCredentials)."""
        auth_manager = SpotifyClientCredentials(
            client_id=self.client_id,
            client_secret=self.client_secret,
        )
        self.sp = spotipy.Spotify(auth_manager=auth_manager, requests_timeout=20)
        self.user_info = None

    def login_oauth(self) -> dict:
        """
        Start OAuth-flow (opent browser). Retourneert user-info dict.
        Gooit een exception als de flow faalt.
        """
        auth_manager = SpotifyOAuth(
            client_id=self.client_id,
            client_secret=self.client_secret,
            redirect_uri=self.redirect_uri,
            scope="playlist-read-private playlist-read-collaborative user-library-read",
            cache_path=SPOTIFY_CACHE_PATH,
            open_browser=True,
        )
        self.sp = spotipy.Spotify(auth_manager=auth_manager, requests_timeout=20)
        self.user_info = self.sp.current_user()
        return self.user_info

    def try_restore_session(self) -> bool:
        """Probeer een eerder opgeslagen OAuth-token te hergebruiken (zonder browser)."""
        try:
            auth_manager = SpotifyOAuth(
                client_id=self.client_id,
                client_secret=self.client_secret,
                redirect_uri=self.redirect_uri,
                scope="playlist-read-private playlist-read-collaborative user-library-read",
                cache_path=SPOTIFY_CACHE_PATH,
                open_browser=False,
            )
            token_info = auth_manager.get_cached_token()
            if token_info:
                self.sp = spotipy.Spotify(auth_manager=auth_manager, requests_timeout=20)
                self.user_info = self.sp.current_user()
                return True
        except Exception:
            pass
        return False

    def logout(self) -> None:
        """Log uit en keer terug naar publieke modus."""
        import os
        try:
            os.remove(SPOTIFY_CACHE_PATH)
        except FileNotFoundError:
            pass
        self._init_public()

    def is_logged_in(self) -> bool:
        return self.user_info is not None

    def get_display_name(self) -> str:
        if self.user_info:
            return self.user_info.get("display_name") or self.user_info.get("id", "Gebruiker")
        return ""

    # ------------------------------------------------------------------
    # URL Parsing
    # ------------------------------------------------------------------

    @staticmethod
    def parse_url(url: str) -> tuple[Optional[str], Optional[str]]:
        """Parse een Spotify URL/URI en retourneer (type, id) of (None, None)."""
        url = url.strip()
        patterns = [
            r"open\.spotify\.com/(?:intl-[a-zA-Z-]+/)?(track|album|playlist)/([a-zA-Z0-9]+)",
            r"spotify:(track|album|playlist):([a-zA-Z0-9]+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1), match.group(2)
        return None, None

    # ------------------------------------------------------------------
    # Metadata ophalen (met volledige paginering)
    # ------------------------------------------------------------------

    @staticmethod
    def _track_dict(track: dict, album_name: str = "", album_art: str = "") -> dict:
        """Maak een genormaliseerd track-woordenboek met alle benodigde metadata."""
        if not track or not isinstance(track, dict) or not track.get("id"):
            return {}

        art_url = album_art
        if not art_url:
            album_obj = track.get("album")
            if isinstance(album_obj, dict):
                album_images = album_obj.get("images", [])
                if album_images and isinstance(album_images, list) and isinstance(album_images[0], dict):
                    art_url = album_images[0].get("url", "")

        raw_name = track.get("name")
        name = raw_name.strip() if isinstance(raw_name, str) and raw_name.strip() else "Onbekend"

        artists_list = [
            a["name"].strip()
            for a in track.get("artists", [])
            if isinstance(a, dict) and isinstance(a.get("name"), str) and a["name"].strip()
        ]
        artists = ", ".join(artists_list) if artists_list else "Onbekend"

        album_obj = track.get("album") if isinstance(track.get("album"), dict) else {}
        album = album_name or album_obj.get("name") or ""
        if not isinstance(album, str):
            album = str(album)

        track_id = track.get("id", "")
        external_urls = track.get("external_urls")
        spotify_url = external_urls.get("spotify") if isinstance(external_urls, dict) else ""
        if not spotify_url and track_id:
            spotify_url = f"https://open.spotify.com/track/{track_id}"

        return {
            "id": track_id,
            "name": name,
            "artists": artists,
            "album": album,
            "album_art": art_url,
            "uri": track.get("uri") or "",
            "url": spotify_url,
            "duration_ms": track.get("duration_ms") or 0,
            "track_number": track.get("track_number") or 0,
            "release_date": album_obj.get("release_date") or "",
        }

    def _paginate(self, page: dict, extract_track) -> list[dict]:
        """Generiek pagineer door een Spotify-resultatenset."""
        tracks = []
        while page:
            for item in page.get("items", []):
                td = extract_track(item)
                if td:
                    tracks.append(td)
            page = self.sp.next(page) if page.get("next") else None
        return tracks

    def get_playlist_tracks(self, playlist_id: str) -> tuple[str, list[dict]]:
        """Haal alle tracks van een playlist op (inclusief paginering)."""
        result = self.sp.playlist(playlist_id)
        name = result.get("name", "Playlist")
        tracks_obj = result.get("tracks") or result.get("items")
        if not tracks_obj:
            tracks_obj = self.sp.playlist_items(playlist_id)
        tracks = self._paginate(
            tracks_obj,
            lambda item: self._track_dict(
                item.get("item") or item.get("track") or item if isinstance(item, dict) else {},
                "",
            ),
        )
        return name, tracks

    def get_album_tracks(self, album_id: str) -> tuple[str, list[dict]]:
        """Haal alle tracks van een album op."""
        album = self.sp.album(album_id)
        album_name = album.get("name", "Album")
        album_images = album.get("images", [])
        album_art = album_images[0]["url"] if album_images else ""
        tracks_obj = album.get("tracks") or album.get("items")
        tracks = self._paginate(
            tracks_obj,
            lambda item: self._track_dict(
                item.get("item") or item.get("track") or item if isinstance(item, dict) else {},
                album_name,
                album_art,
            ),
        )
        return album_name, tracks

    def get_track(self, track_id: str) -> tuple[str, list[dict]]:
        """Haal metadata op voor een enkel nummer."""
        track = self.sp.track(track_id)
        td = self._track_dict(track)
        title = f"{td['artists']} - {td['name']}" if td else "Track"
        return title, [td] if td else []

    def get_liked_songs(self) -> tuple[str, list[dict]]:
        """Haal de 'Liked Songs' van de ingelogde gebruiker op."""
        if not self.is_logged_in():
            raise PermissionError("Je moet ingelogd zijn om Liked Songs op te halen.")
        page = self.sp.current_user_saved_tracks(limit=50)
        tracks = self._paginate(
            page,
            lambda item: self._track_dict(
                item.get("item") or item.get("track") or item if isinstance(item, dict) else {},
                "",
            ),
        )
        return "Liked Songs", tracks

    def get_user_playlists(self) -> list[dict]:
        """Haal alle playlists van de ingelogde gebruiker op."""
        if not self.is_logged_in():
            raise PermissionError("Je moet ingelogd zijn om playlists op te halen.")
        playlists = []
        page = self.sp.current_user_playlists(limit=50)
        while page:
            for item in page.get("items", []):
                playlists.append({
                    "id": item["id"],
                    "name": item["name"],
                    "owner": item.get("owner", {}).get("display_name", ""),
                    "tracks_total": item.get("tracks", {}).get("total", 0),
                    "url": item.get("external_urls", {}).get("spotify", ""),
                })
            page = self.sp.next(page) if page.get("next") else None
        return playlists

    def fetch_from_url(self, url: str) -> tuple[str, list[dict]]:
        """Haal tracks op gebaseerd op een Spotify URL. Retourneert (naam, [tracks])."""
        content_type, content_id = self.parse_url(url)
        if content_type == "playlist":
            return self.get_playlist_tracks(content_id)
        elif content_type == "album":
            return self.get_album_tracks(content_id)
        elif content_type == "track":
            return self.get_track(content_id)
        else:
            raise ValueError(
                "Ongeldige Spotify URL. Gebruik een link naar een playlist, album of track.\n"
                f"Ontvangen: {url}"
            )
