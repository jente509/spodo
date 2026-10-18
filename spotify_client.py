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
        self.user_info = None
        if not self.client_id or not self.client_secret:
            self.sp = None
            return
        try:
            auth_manager = SpotifyClientCredentials(
                client_id=self.client_id,
                client_secret=self.client_secret,
            )
            self.sp = spotipy.Spotify(auth_manager=auth_manager, requests_timeout=20)
        except Exception:
            self.sp = None

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

    # ------------------------------------------------------------------
    # Web Scraper & Embed Fallback Helpers
    # (voor wanneer Spotify Web API 403 Forbidden of 404 geeft door API-beperkingen)
    # ------------------------------------------------------------------

    def _scrape_playlist(self, playlist_id: str) -> tuple[str, list[dict]]:
        """Haal tracks van een playlist op via spotifyscraper of embed fallback."""
        try:
            from spotify_scraper import SpotifyClient as ScraperClient
            with ScraperClient() as client:
                p = client.get_playlist(playlist_id, max_tracks=None)
                name = p.name or "Playlist"
                tracks = []
                for item in p.tracks:
                    t = item.track
                    if not t or not getattr(t, "id", None):
                        continue
                    art_url = t.images[0].url if t.images else ""
                    if not art_url and t.album and getattr(t.album, "images", None):
                        art_url = t.album.images[0].url
                    album_name = t.album.name if t.album else ""
                    artists = ", ".join([a.name for a in t.artists]) if t.artists else "Onbekend"
                    tracks.append({
                        "id": t.id,
                        "name": t.name or "Onbekend",
                        "artists": artists,
                        "album": album_name,
                        "album_art": art_url,
                        "uri": getattr(t, "uri", "") or f"spotify:track:{t.id}",
                        "url": f"https://open.spotify.com/track/{t.id}",
                        "duration_ms": getattr(t, "duration_ms", 0) or 0,
                        "track_number": getattr(t, "track_number", 0) or 0,
                        "release_date": str(getattr(t, "release_date", "") or ""),
                    })
                if tracks:
                    return name, tracks
        except Exception:
            pass

        return self._scrape_playlist_embed(playlist_id)

    def _scrape_playlist_embed(self, playlist_id: str) -> tuple[str, list[dict]]:
        """Directe extractie via Spotify Embed Next.js data."""
        import json
        import requests
        url = f"https://open.spotify.com/embed/playlist/{playlist_id}"
        r = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
            timeout=15,
        )
        m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', r.text, re.DOTALL)
        if not m:
            raise ValueError(f"Kon playlist {playlist_id} niet ophalen (pagina onbereikbaar).")
        data = json.loads(m.group(1))
        entity = data.get("props", {}).get("pageProps", {}).get("state", {}).get("data", {}).get("entity", {})
        name = entity.get("name") or entity.get("title") or "Playlist"
        cover_art = ""
        sources = entity.get("coverArt", {}).get("sources", [])
        if sources and sources[0].get("url"):
            cover_art = sources[0]["url"]

        tracks = []
        for item in entity.get("trackList", []):
            uri = item.get("uri", "")
            tid = uri.split(":")[-1] if uri else item.get("uid", "")
            title = item.get("title") or "Onbekend"
            subtitle = item.get("subtitle") or "Onbekend"
            artists = subtitle.replace("\u00a0", " ").strip()
            tracks.append({
                "id": tid,
                "name": title,
                "artists": artists,
                "album": name,
                "album_art": cover_art,
                "uri": uri,
                "url": f"https://open.spotify.com/track/{tid}" if tid else "",
                "duration_ms": item.get("duration") or 0,
                "track_number": len(tracks) + 1,
                "release_date": "",
            })
        if not tracks:
            raise ValueError(f"Geen nummers gevonden in playlist {playlist_id}.")
        return name, tracks

    def _scrape_album(self, album_id: str) -> tuple[str, list[dict]]:
        """Haal tracks van een album op via scraper of embed."""
        try:
            from spotify_scraper import SpotifyClient as ScraperClient
            with ScraperClient() as client:
                a = client.get_album(album_id)
                album_name = a.name or "Album"
                art_url = a.images[0].url if a.images else ""
                tracks = []
                for t in a.tracks:
                    if not t or not getattr(t, "id", None):
                        continue
                    artists = ", ".join([art.name for art in t.artists]) if t.artists else "Onbekend"
                    tracks.append({
                        "id": t.id,
                        "name": t.name or "Onbekend",
                        "artists": artists,
                        "album": album_name,
                        "album_art": art_url,
                        "uri": getattr(t, "uri", "") or f"spotify:track:{t.id}",
                        "url": f"https://open.spotify.com/track/{t.id}",
                        "duration_ms": getattr(t, "duration_ms", 0) or 0,
                        "track_number": getattr(t, "track_number", 0) or 0,
                        "release_date": str(getattr(a, "release_date", "") or ""),
                    })
                if tracks:
                    return album_name, tracks
        except Exception:
            pass

        import json
        import requests
        url = f"https://open.spotify.com/embed/album/{album_id}"
        r = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
            timeout=15,
        )
        m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', r.text, re.DOTALL)
        if not m:
            raise ValueError(f"Kon album {album_id} niet ophalen.")
        data = json.loads(m.group(1))
        entity = data.get("props", {}).get("pageProps", {}).get("state", {}).get("data", {}).get("entity", {})
        album_name = entity.get("name") or entity.get("title") or "Album"
        cover_art = ""
        visual = entity.get("visualIdentity", {}).get("image", [])
        if visual and visual[0].get("url"):
            cover_art = visual[0]["url"]

        tracks = []
        for item in entity.get("trackList", []):
            uri = item.get("uri", "")
            tid = uri.split(":")[-1] if uri else item.get("uid", "")
            title = item.get("title") or "Onbekend"
            subtitle = item.get("subtitle") or "Onbekend"
            artists = subtitle.replace("\u00a0", " ").strip()
            tracks.append({
                "id": tid,
                "name": title,
                "artists": artists,
                "album": album_name,
                "album_art": cover_art,
                "uri": uri,
                "url": f"https://open.spotify.com/track/{tid}" if tid else "",
                "duration_ms": item.get("duration") or 0,
                "track_number": len(tracks) + 1,
                "release_date": str(entity.get("releaseDate") or ""),
            })
        return album_name, tracks

    def _scrape_track(self, track_id: str) -> tuple[str, list[dict]]:
        """Haal metadata van een losse track op via scraper of embed."""
        try:
            from spotify_scraper import SpotifyClient as ScraperClient
            with ScraperClient() as client:
                t = client.get_track(track_id)
                art_url = t.images[0].url if t.images else ""
                if not art_url and t.album and getattr(t.album, "images", None):
                    art_url = t.album.images[0].url
                album_name = t.album.name if t.album else ""
                artists = ", ".join([art.name for art in t.artists]) if t.artists else "Onbekend"
                td = {
                    "id": t.id,
                    "name": t.name or "Onbekend",
                    "artists": artists,
                    "album": album_name,
                    "album_art": art_url,
                    "uri": getattr(t, "uri", "") or f"spotify:track:{t.id}",
                    "url": f"https://open.spotify.com/track/{t.id}",
                    "duration_ms": getattr(t, "duration_ms", 0) or 0,
                    "track_number": getattr(t, "track_number", 0) or 0,
                    "release_date": str(getattr(t, "release_date", "") or ""),
                }
                title = f"{artists} - {t.name}"
                return title, [td]
        except Exception:
            pass

        import json
        import requests
        url = f"https://open.spotify.com/embed/track/{track_id}"
        r = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
            timeout=15,
        )
        m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', r.text, re.DOTALL)
        if not m:
            raise ValueError(f"Kon track {track_id} niet ophalen.")
        data = json.loads(m.group(1))
        entity = data.get("props", {}).get("pageProps", {}).get("state", {}).get("data", {}).get("entity", {})
        title = entity.get("name") or entity.get("title") or "Track"
        artists_list = [a.get("name") for a in entity.get("artists", []) if a.get("name")]
        artists = ", ".join(artists_list) if artists_list else "Onbekend"
        cover_art = ""
        visual = entity.get("visualIdentity", {}).get("image", [])
        if visual and visual[0].get("url"):
            cover_art = visual[0]["url"]
        td = {
            "id": track_id,
            "name": title,
            "artists": artists,
            "album": "",
            "album_art": cover_art,
            "uri": f"spotify:track:{track_id}",
            "url": f"https://open.spotify.com/track/{track_id}",
            "duration_ms": entity.get("duration") or 0,
            "track_number": 1,
            "release_date": str(entity.get("releaseDate") or ""),
        }
        return f"{artists} - {title}", [td]

    def get_playlist_tracks(self, playlist_id: str) -> tuple[str, list[dict]]:
        """Haal alle tracks van een playlist op (inclusief paginering en automatische fallback)."""
        if self.sp:
            try:
                result = self.sp.playlist(playlist_id)
                name = result.get("name", "Playlist")
                tracks_obj = result.get("tracks")
                if not tracks_obj:
                    tracks_obj = self.sp.playlist_items(playlist_id, additional_types=("track",))
                tracks = self._paginate(
                    tracks_obj,
                    lambda item: self._track_dict(
                        item.get("item") or item.get("track") or item if isinstance(item, dict) else {},
                        "",
                    ),
                )
                if tracks:
                    return name, tracks
            except Exception:
                # Als Spotify API faalt (bv. 403 Forbidden bij third-party playlists of 404 bij Spotify-curated)
                pass

        return self._scrape_playlist(playlist_id)

    def get_album_tracks(self, album_id: str) -> tuple[str, list[dict]]:
        """Haal alle tracks van een album op met fallback."""
        if self.sp:
            try:
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
                if tracks:
                    return album_name, tracks
            except Exception:
                pass

        return self._scrape_album(album_id)

    def get_track(self, track_id: str) -> tuple[str, list[dict]]:
        """Haal metadata op voor een enkel nummer met fallback."""
        if self.sp:
            try:
                track = self.sp.track(track_id)
                td = self._track_dict(track)
                if td:
                    title = f"{td['artists']} - {td['name']}"
                    return title, [td]
            except Exception:
                pass

        return self._scrape_track(track_id)

    def get_liked_songs(self) -> tuple[str, list[dict]]:
        """Haal de 'Liked Songs' van de ingelogde gebruiker op."""
        if not self.is_logged_in():
            raise PermissionError("Je moet ingelogd zijn om Liked Songs op te halen.")
        try:
            page = self.sp.current_user_saved_tracks(limit=50)
            tracks = self._paginate(
                page,
                lambda item: self._track_dict(
                    item.get("item") or item.get("track") or item if isinstance(item, dict) else {},
                    "",
                ),
            )
        except Exception as exc:
            raise RuntimeError(
                f"Kon Liked Songs niet ophalen via Spotify API: {exc}\n"
                "Controleer je internetverbinding of log opnieuw in."
            ) from exc
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
