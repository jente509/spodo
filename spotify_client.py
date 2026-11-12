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

    def _build_oauth(self, open_browser: bool = False) -> SpotifyOAuth:
        """Maak een geconfigureerde SpotifyOAuth manager."""
        return SpotifyOAuth(
            client_id=self.client_id,
            client_secret=self.client_secret,
            redirect_uri=self.redirect_uri or "http://127.0.0.1:3001/api/callback",
            scope="playlist-read-private playlist-read-collaborative user-library-read",
            cache_path=SPOTIFY_CACHE_PATH,
            open_browser=open_browser,
        )

    def login_oauth(self) -> dict:
        """
        Start OAuth-flow (opent browser). Retourneert user-info dict.
        Gooit een exception als de flow faalt.
        """
        if not self.client_id or not self.client_secret:
            raise ValueError("Client ID and Client Secret are required to log in.")
        try:
            auth_manager = self._build_oauth(open_browser=True)
            sp = spotipy.Spotify(auth_manager=auth_manager, requests_timeout=20)
            user_info = sp.current_user()
            self.sp = sp
            self.user_info = user_info
            return self.user_info
        except Exception:
            self._init_public()
            raise

    def try_restore_session(self) -> bool:
        """Probeer een eerder opgeslagen OAuth-token te hergebruiken (zonder browser)."""
        if not self.client_id or not self.client_secret:
            return False
        import os
        if not os.path.exists(SPOTIFY_CACHE_PATH):
            return False
        try:
            auth_manager = self._build_oauth(open_browser=False)
            token_info = auth_manager.get_cached_token()
            if token_info:
                sp = spotipy.Spotify(auth_manager=auth_manager, requests_timeout=20)
                user_info = sp.current_user()
                self.sp = sp
                self.user_info = user_info
                return True
        except Exception:
            # Verwijder corrupte of verlopen cache zodat volgende login schoon start
            try:
                os.remove(SPOTIFY_CACHE_PATH)
            except OSError:
                pass
            self._init_public()
        return False

    def logout(self) -> None:
        """Log uit en keer terug naar publieke modus."""
        import os
        self.user_info = None
        try:
            os.remove(SPOTIFY_CACHE_PATH)
        except FileNotFoundError:
            pass
        self._init_public()

    def is_logged_in(self) -> bool:
        return self.user_info is not None

    def get_display_name(self) -> str:
        if self.user_info:
            return self.user_info.get("display_name") or self.user_info.get("id", "User")
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
    def _track_dict(
        track: dict,
        album_name: str = "",
        album_art: str = "",
        release_date: str = "",
    ) -> dict:
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
            "release_date": release_date or album_obj.get("release_date") or "",
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
        r.raise_for_status()
        m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', r.text, re.DOTALL)
        if not m:
            raise ValueError(f"Could not fetch playlist {playlist_id} (page unreachable).")
        data = json.loads(m.group(1))
        entity = ((data.get("props") or {}).get("pageProps") or {}).get("state", {}).get("data", {}).get("entity") or {}
        name = entity.get("name") or entity.get("title") or "Playlist"
        cover_art = ""
        sources = (entity.get("coverArt") or {}).get("sources") or []
        if sources and isinstance(sources[0], dict) and sources[0].get("url"):
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
            raise ValueError(f"No tracks found in playlist {playlist_id}.")
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
        r.raise_for_status()
        m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', r.text, re.DOTALL)
        if not m:
            raise ValueError(f"Could not fetch album {album_id}.")
        data = json.loads(m.group(1))
        entity = ((data.get("props") or {}).get("pageProps") or {}).get("state", {}).get("data", {}).get("entity") or {}
        album_name = entity.get("name") or entity.get("title") or "Album"
        cover_art = ""
        visual = (entity.get("visualIdentity") or {}).get("image") or []
        if visual and isinstance(visual[0], dict) and visual[0].get("url"):
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
        r.raise_for_status()
        m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', r.text, re.DOTALL)
        if not m:
            raise ValueError(f"Could not fetch track {track_id}.")
        data = json.loads(m.group(1))
        entity = ((data.get("props") or {}).get("pageProps") or {}).get("state", {}).get("data", {}).get("entity") or {}
        title = entity.get("name") or entity.get("title") or "Track"
        artists_list = [a.get("name") for a in (entity.get("artists") or []) if isinstance(a, dict) and a.get("name")]
        artists = ", ".join(artists_list) if artists_list else "Onbekend"
        cover_art = ""
        visual = (entity.get("visualIdentity") or {}).get("image") or []
        if visual and isinstance(visual[0], dict) and visual[0].get("url"):
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
                album_images = album.get("images") or []
                album_art = album_images[0]["url"] if album_images and isinstance(album_images[0], dict) else ""
                album_release = str(album.get("release_date") or "")
                tracks_obj = album.get("tracks") or album.get("items")
                tracks = self._paginate(
                    tracks_obj,
                    lambda item: self._track_dict(
                        item.get("item") or item.get("track") or item if isinstance(item, dict) else {},
                        album_name,
                        album_art,
                        album_release,
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
            raise PermissionError("You must be logged in to fetch Liked Songs.")
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
                f"Could not fetch Liked Songs via Spotify API: {exc}\n"
                "Check your internet connection or log in again."
            ) from exc
        return "Liked Songs", tracks

    def get_user_playlists(self) -> list[dict]:
        """Haal alle playlists van de ingelogde gebruiker op."""
        if not self.is_logged_in():
            raise PermissionError("You must be logged in to fetch playlists.")
        playlists = []
        try:
            page = self.sp.current_user_playlists(limit=50)
            while page:
                for item in page.get("items") or []:
                    if not item or not isinstance(item, dict):
                        continue
                    owner_obj = item.get("owner") or {}
                    tracks_obj = item.get("tracks") or item.get("items") or {}
                    ext_urls = item.get("external_urls") or {}
                    playlists.append({
                        "id": item.get("id", ""),
                        "name": item.get("name") or "Playlist",
                        "owner": owner_obj.get("display_name", "") if isinstance(owner_obj, dict) else "",
                        "tracks_total": tracks_obj.get("total", 0) if isinstance(tracks_obj, dict) else 0,
                        "url": ext_urls.get("spotify", "") if isinstance(ext_urls, dict) else "",
                    })
                page = self.sp.next(page) if page.get("next") else None
        except Exception as exc:
            raise RuntimeError(
                f"Could not fetch playlists via Spotify API: {exc}\n"
                "Check your internet connection or log in again."
            ) from exc
        return playlists

    @staticmethod
    def _resolve_shortlink(url: str) -> str:
        """Volg Spotify-shortlinks (spotify.link / spoti.fi) naar de echte open.spotify.com URL."""
        if "spotify.link" in url or "spoti.fi" in url:
            try:
                import requests
                resp = requests.get(
                    url,
                    allow_redirects=True,
                    timeout=10,
                    headers={"User-Agent": "Mozilla/5.0"},
                )
                if resp.url and "open.spotify.com" in resp.url:
                    return resp.url
            except Exception:
                pass
        return url

    def fetch_from_url(self, url: str) -> tuple[str, list[dict]]:
        """Haal tracks op gebaseerd op een Spotify URL. Retourneert (naam, [tracks])."""
        resolved_url = self._resolve_shortlink(url.strip())
        content_type, content_id = self.parse_url(resolved_url)
        if content_type == "playlist":
            return self.get_playlist_tracks(content_id)
        elif content_type == "album":
            return self.get_album_tracks(content_id)
        elif content_type == "track":
            return self.get_track(content_id)
        else:
            raise ValueError(
                "Invalid Spotify URL. Please use a link to a playlist, album, or track.\n"
                f"Received: {url}"
            )
