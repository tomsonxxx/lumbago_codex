from __future__ import annotations

from dataclasses import dataclass
from html import unescape
from typing import Callable
import re
from urllib.parse import quote_plus

import requests


@dataclass
class PortalCandidate:
    source_key: str
    source_label: str
    title: str | None = None
    artist: str | None = None
    album: str | None = None
    genre: str | None = None
    year: str | None = None
    publisher: str | None = None
    url: str | None = None


@dataclass
class PortalProbe:
    source_key: str
    source_label: str
    candidate: PortalCandidate | None
    detail: str


class FreeMusicPortalSearch:
    """Search music metadata in popular free portals without paid plans."""

    PORTALS: tuple[tuple[str, str], ...] = (
        ("deezer", "Deezer"),
        ("itunes", "Apple Music/iTunes"),
        ("listenbrainz", "ListenBrainz"),
        ("theaudiodb", "TheAudioDB"),
        ("lastfm", "Last.fm"),
        ("musixmatch", "Musixmatch"),
        ("genius", "Genius"),
        ("musicbrainz_portal", "MusicBrainz"),
        ("discogs_portal", "Discogs"),
        ("youtube", "YouTube"),
        ("soundcloud", "SoundCloud"),
        ("bandcamp", "Bandcamp"),
        ("audius", "Audius"),
        ("archiveorg", "Internet Archive"),
        ("jiosaavn", "JioSaavn"),
    )

    _SOUNDCLOUD_CLIENT_ID: str | None = None

    def __init__(
        self,
        musicbrainz_app_name: str | None = None,
        discogs_token: str | None = None,
        lastfm_api_key: str | None = None,
        musixmatch_api_key: str | None = None,
        genius_api_key: str | None = None,
        timeout: float = 7.0,
    ) -> None:
        self.musicbrainz_app_name = musicbrainz_app_name or "LumbagoMusicAI"
        self.discogs_token = discogs_token
        self.lastfm_api_key = lastfm_api_key
        self.musixmatch_api_key = musixmatch_api_key
        self.genius_api_key = genius_api_key
        self.timeout = timeout
        self.session = requests.Session()
        self.user_agent = "LumbagoMusicAI/1.0"
        self._providers: dict[str, Callable[[str], PortalProbe]] = {
            "deezer": self._search_deezer,
            "itunes": self._search_itunes,
            "listenbrainz": self._search_listenbrainz,
            "theaudiodb": self._search_theaudiodb,
            "lastfm": self._search_lastfm,
            "musixmatch": self._search_musixmatch,
            "genius": self._search_genius,
            "musicbrainz_portal": self._search_musicbrainz,
            "discogs_portal": self._search_discogs,
            "youtube": self._search_youtube,
            "soundcloud": self._search_soundcloud,
            "bandcamp": self._search_bandcamp,
            "audius": self._search_audius,
            "archiveorg": self._search_archiveorg,
            "jiosaavn": self._search_jiosaavn,
        }

    def search_all(self, query: str) -> list[PortalProbe]:
        probes: list[PortalProbe] = []
        for key, label in self.PORTALS:
            provider = self._providers.get(key)
            if provider is None:
                probes.append(PortalProbe(key, label, None, "Provider not configured"))
                continue
            try:
                probe = provider(query)
            except Exception as exc:  # defensive: one bad portal must not break the pipeline
                probe = PortalProbe(key, label, None, f"Error: {exc}")
            probes.append(probe)
        return probes

    # ------------------------------------------------------------------
    # Nowe źródła
    # ------------------------------------------------------------------

    def _search_listenbrainz(self, query: str) -> PortalProbe:
        """ListenBrainz metadata lookup — bezpłatne, bez klucza API.

        Używa endpointu /1/metadata/lookup, który agreguje dane
        MusicBrainz w jednym żądaniu (tytuł, wykonawca, album, rok, label).
        """
        key, label = "listenbrainz", "ListenBrainz"
        artist, title = _split_query(query)
        if not title:
            return PortalProbe(key, label, None, "Nie można podzielić zapytania")
        try:
            resp = self.session.get(
                "https://api.listenbrainz.org/1/metadata/lookup",
                params={"artist_name": artist or "", "recording_name": title, "inc": "artist release"},
                timeout=self.timeout,
                headers={"User-Agent": self.user_agent},
            )
        except Exception as exc:
            return PortalProbe(key, label, None, f"Błąd: {exc}")
        if resp.status_code != 200:
            return PortalProbe(key, label, None, f"HTTP {resp.status_code}")
        data = resp.json()
        recording = data.get("recording") or {}
        release = recording.get("release") or data.get("release") or {}
        artist_data = recording.get("artist") or data.get("artist") or {}
        rec_title = recording.get("name") or data.get("recording_name")
        artist_name = (
            artist_data.get("name")
            or (artist_data.get("artists") or [{}])[0].get("name")
        )
        release_date = str(release.get("date") or release.get("release_date") or "")
        year = release_date[:4] if release_date[:4].isdigit() else None
        if not rec_title and not artist_name:
            return PortalProbe(key, label, None, "Brak wyników")
        candidate = PortalCandidate(
            source_key=key,
            source_label=label,
            title=rec_title,
            artist=artist_name,
            album=release.get("name") or release.get("title"),
            year=year,
            publisher=(release.get("label") or {}).get("name"),
            url=(
                f"https://musicbrainz.org/recording/{recording.get('mbid')}"
                if recording.get("mbid") else None
            ),
        )
        return PortalProbe(key, label, candidate, "OK")

    def _search_theaudiodb(self, query: str) -> PortalProbe:
        """TheAudioDB — bezpłatny klucz publiczny '2'.

        Zwraca gatunek, nastrój (mood), BPM i rok — dane bardzo
        cenne dla DJ-ów. Endpoint: searchtrack.php?s=artist&t=track.
        """
        key, label = "theaudiodb", "TheAudioDB"
        artist, title = _split_query(query)
        params: dict[str, str] = {}
        if artist and title:
            params = {"s": artist, "t": title}
        elif title:
            params = {"s": "", "t": title}
        else:
            params = {"s": query}
        try:
            resp = self.session.get(
                "https://www.theaudiodb.com/api/v1/json/2/searchtrack.php",
                params=params,
                timeout=self.timeout,
                headers={"User-Agent": self.user_agent},
            )
        except Exception as exc:
            return PortalProbe(key, label, None, f"Błąd: {exc}")
        if resp.status_code != 200:
            return PortalProbe(key, label, None, f"HTTP {resp.status_code}")
        tracks = (resp.json() or {}).get("track") or []
        if not tracks:
            return PortalProbe(key, label, None, "Brak wyników")
        item = tracks[0]
        # Jeśli genre jest puste, użyj mood jako uzupełnienie (oba są przydatne dla DJ-ów)
        genre = item.get("strGenre") or item.get("strMood")
        candidate = PortalCandidate(
            source_key=key,
            source_label=label,
            title=item.get("strTrack"),
            artist=item.get("strArtist"),
            album=item.get("strAlbum"),
            genre=genre,
            year=str(item.get("intYearReleased") or "") or None,
            publisher=item.get("strLabel"),
            url=item.get("strMusicVid") or item.get("strTrackThumb"),
        )
        return PortalProbe(key, label, candidate, "OK")

    def _search_lastfm(self, query: str) -> PortalProbe:
        """Last.fm Track Search — bezpłatny klucz API (rejestracja na last.fm).

        Zwraca gatunek (tagi), album, rok i liczbę odsłuchań.
        Jeśli klucz nie jest skonfigurowany, portal jest pomijany.
        """
        key, label = "lastfm", "Last.fm"
        if not self.lastfm_api_key:
            return PortalProbe(key, label, None, "Brak klucza LASTFM_API_KEY")
        artist, title = _split_query(query)
        method = "track.getInfo" if (artist and title) else "track.search"
        params: dict[str, str] = {
            "api_key": self.lastfm_api_key,
            "format": "json",
            "limit": "1",
        }
        if method == "track.getInfo":
            params.update({"method": "track.getInfo", "artist": artist, "track": title})
        else:
            params.update({"method": "track.search", "track": query})
        try:
            resp = self.session.get(
                "https://ws.audioscrobbler.com/2.0/",
                params=params,
                timeout=self.timeout,
                headers={"User-Agent": self.user_agent},
            )
        except Exception as exc:
            return PortalProbe(key, label, None, f"Błąd: {exc}")
        if resp.status_code != 200:
            return PortalProbe(key, label, None, f"HTTP {resp.status_code}")
        data = resp.json()
        if method == "track.getInfo":
            item = data.get("track") or {}
            if not item:
                return PortalProbe(key, label, None, "Brak wyników")
            album_data = item.get("album") or {}
            tags = [t.get("name") for t in (item.get("toptags") or {}).get("tag", []) if t.get("name")]
            genre = tags[0] if tags else None
            year = str(album_data.get("@attr", {}).get("position") or "")[:4] or None
            candidate = PortalCandidate(
                source_key=key, source_label=label,
                title=item.get("name"),
                artist=(item.get("artist") or {}).get("name") or item.get("artist"),
                album=album_data.get("title"),
                genre=genre,
                url=item.get("url"),
            )
        else:
            matches = data.get("results", {}).get("trackmatches", {}).get("track", [])
            if not matches:
                return PortalProbe(key, label, None, "Brak wyników")
            item = matches[0] if isinstance(matches, list) else matches
            candidate = PortalCandidate(
                source_key=key, source_label=label,
                title=item.get("name"),
                artist=item.get("artist"),
                url=item.get("url"),
            )
        return PortalProbe(key, label, candidate, "OK")

    def _search_musixmatch(self, query: str) -> PortalProbe:
        """Musixmatch Track Search — bezpłatny klucz API (2000 req/dzień).

        Zwraca tytuł, artystę, album, gatunek i rok. Bezpłatna rejestracja
        na developer.musixmatch.com.
        """
        key, label = "musixmatch", "Musixmatch"
        if not self.musixmatch_api_key:
            return PortalProbe(key, label, None, "Brak klucza MUSIXMATCH_API_KEY")
        artist, title = _split_query(query)
        params: dict[str, str] = {
            "apikey": self.musixmatch_api_key,
            "page_size": "1",
            "page": "1",
            "s_track_rating": "desc",
        }
        if artist and title:
            params.update({"q_track": title, "q_artist": artist})
        else:
            params["q_track"] = query
        try:
            resp = self.session.get(
                "https://api.musixmatch.com/ws/1.1/track.search",
                params=params,
                timeout=self.timeout,
                headers={"User-Agent": self.user_agent},
            )
        except Exception as exc:
            return PortalProbe(key, label, None, f"Błąd: {exc}")
        if resp.status_code != 200:
            return PortalProbe(key, label, None, f"HTTP {resp.status_code}")
        body = resp.json()
        track_list = (
            (body.get("message") or {})
            .get("body", {})
            .get("track_list", [])
        )
        if not track_list:
            return PortalProbe(key, label, None, "Brak wyników")
        item = track_list[0].get("track", {})
        date_str = str(item.get("first_release_date") or "")
        year = date_str[:4] if date_str[:4].isdigit() else None
        genres = item.get("primary_genres", {}).get("music_genre_list", [])
        genre = (genres[0].get("music_genre", {}).get("music_genre_name")) if genres else None
        candidate = PortalCandidate(
            source_key=key, source_label=label,
            title=item.get("track_name"),
            artist=item.get("artist_name"),
            album=item.get("album_name"),
            genre=genre,
            year=year,
            url=item.get("track_share_url"),
        )
        return PortalProbe(key, label, candidate, "OK")

    def _search_genius(self, query: str) -> PortalProbe:
        """Genius Track Search — bezpłatny token API (rejestracja na genius.com/api-clients).

        Zwraca tytuł, artystę i URL z bogatymi danymi tekstowymi.
        Jeśli token nie jest skonfigurowany, portal jest pomijany.
        """
        key, label = "genius", "Genius"
        if not self.genius_api_key:
            return PortalProbe(key, label, None, "Brak klucza GENIUS_API_KEY")
        try:
            resp = self.session.get(
                "https://api.genius.com/search",
                params={"q": query, "per_page": "1"},
                timeout=self.timeout,
                headers={
                    "User-Agent": self.user_agent,
                    "Authorization": f"Bearer {self.genius_api_key}",
                },
            )
        except Exception as exc:
            return PortalProbe(key, label, None, f"Błąd: {exc}")
        if resp.status_code != 200:
            return PortalProbe(key, label, None, f"HTTP {resp.status_code}")
        hits = (
            (resp.json().get("response") or {})
            .get("hits", [])
        )
        if not hits:
            return PortalProbe(key, label, None, "Brak wyników")
        result = hits[0].get("result") or {}
        primary = result.get("primary_artist") or {}
        date_str = str(result.get("release_date_for_display") or result.get("release_date") or "")
        year = date_str[-4:] if len(date_str) >= 4 and date_str[-4:].isdigit() else None
        candidate = PortalCandidate(
            source_key=key, source_label=label,
            title=result.get("title") or result.get("full_title"),
            artist=primary.get("name"),
            year=year,
            url=result.get("url"),
        )
        return PortalProbe(key, label, candidate, "OK")

    def _search_youtube(self, query: str) -> PortalProbe:
        key, label = "youtube", "YouTube"
        url = f"https://www.youtube.com/results?search_query={quote_plus(query)}"
        resp = self.session.get(url, timeout=self.timeout, headers={"User-Agent": self.user_agent})
        if resp.status_code != 200:
            return PortalProbe(key, label, None, f"HTTP {resp.status_code}")
        text = resp.text
        vid = re.search(r'"videoId":"([^"]{11})"', text)
        if not vid:
            return PortalProbe(key, label, None, "Brak wyników")
        start = vid.start()
        chunk = text[start : start + 40000]
        title = _extract_between(chunk, '"title":{"runs":[{"text":"', '"')
        artist = _extract_between(chunk, '"longBylineText":{"runs":[{"text":"', '"')
        if not artist:
            artist = _extract_between(chunk, '"ownerText":{"runs":[{"text":"', '"')
        candidate = PortalCandidate(
            source_key=key,
            source_label=label,
            title=unescape(title) if title else None,
            artist=unescape(artist) if artist else None,
            url=f"https://www.youtube.com/watch?v={vid.group(1)}",
        )
        return PortalProbe(key, label, candidate, "OK")

    def _search_soundcloud(self, query: str) -> PortalProbe:
        key, label = "soundcloud", "SoundCloud"
        client_id = self._discover_soundcloud_client_id()
        if not client_id:
            return PortalProbe(key, label, None, "Brak client_id")
        url = "https://api-v2.soundcloud.com/search/tracks"
        resp = self.session.get(
            url,
            params={"q": query, "client_id": client_id, "limit": "1"},
            timeout=self.timeout,
            headers={"User-Agent": self.user_agent, "Accept": "application/json"},
        )
        if resp.status_code != 200:
            return PortalProbe(key, label, None, f"HTTP {resp.status_code}")
        payload = resp.json()
        collection = payload.get("collection", [])
        if not collection:
            return PortalProbe(key, label, None, "Brak wyników")
        item = collection[0]
        user = item.get("user") or {}
        release_date = str(item.get("release_date") or item.get("created_at") or "")
        year = release_date[:4] if release_date[:4].isdigit() else None
        candidate = PortalCandidate(
            source_key=key,
            source_label=label,
            title=item.get("title"),
            artist=user.get("username"),
            genre=item.get("genre"),
            year=year,
            publisher=user.get("username"),
            url=item.get("permalink_url"),
        )
        return PortalProbe(key, label, candidate, "OK")

    def _search_bandcamp(self, query: str) -> PortalProbe:
        key, label = "bandcamp", "Bandcamp"
        url = f"https://bandcamp.com/search?q={quote_plus(query)}&item_type=t"
        resp = self.session.get(url, timeout=self.timeout, headers={"User-Agent": self.user_agent})
        if resp.status_code != 200:
            return PortalProbe(key, label, None, f"HTTP {resp.status_code}")
        block_match = re.search(r'<li class="searchresult data-search".*?</li>', resp.text, re.S)
        if not block_match:
            return PortalProbe(key, label, None, "Brak wyników")
        block = block_match.group(0)
        title = _extract_after_regex(block, r'<div class="heading">\s*<a[^>]*>\s*', r'\s*</a>')
        byline = _extract_after_regex(block, r'<div class="subhead">\s*by\s*', r'\s*</div>')
        href = _extract_after_regex(block, r'<a class="artcont" href="', r'"')
        candidate = PortalCandidate(
            source_key=key,
            source_label=label,
            title=_clean_html_text(title),
            artist=_clean_html_text(byline),
            url=unescape(href) if href else None,
        )
        return PortalProbe(key, label, candidate, "OK")

    def _search_deezer(self, query: str) -> PortalProbe:
        key, label = "deezer", "Deezer"
        resp = self.session.get(
            "https://api.deezer.com/search",
            params={"q": query, "limit": "1"},
            timeout=self.timeout,
            headers={"User-Agent": self.user_agent},
        )
        if resp.status_code != 200:
            return PortalProbe(key, label, None, f"HTTP {resp.status_code}")
        payload = resp.json()
        data = payload.get("data", [])
        if not data:
            return PortalProbe(key, label, None, "Brak wyników")
        item = data[0]
        release_date = str(item.get("release_date") or "")
        year = release_date[:4] if release_date[:4].isdigit() else None
        candidate = PortalCandidate(
            source_key=key,
            source_label=label,
            title=item.get("title_short") or item.get("title"),
            artist=(item.get("artist") or {}).get("name"),
            album=(item.get("album") or {}).get("title"),
            year=year,
            url=item.get("link"),
        )
        return PortalProbe(key, label, candidate, "OK")

    def _search_itunes(self, query: str) -> PortalProbe:
        key, label = "itunes", "Apple Music/iTunes"
        resp = self.session.get(
            "https://itunes.apple.com/search",
            params={"term": query, "entity": "song", "limit": "1"},
            timeout=self.timeout,
            headers={"User-Agent": self.user_agent},
        )
        if resp.status_code != 200:
            return PortalProbe(key, label, None, f"HTTP {resp.status_code}")
        payload = resp.json()
        results = payload.get("results", [])
        if not results:
            return PortalProbe(key, label, None, "Brak wyników")
        item = results[0]
        date = str(item.get("releaseDate") or "")
        year = date[:4] if date[:4].isdigit() else None
        candidate = PortalCandidate(
            source_key=key,
            source_label=label,
            title=item.get("trackName"),
            artist=item.get("artistName"),
            album=item.get("collectionName"),
            genre=item.get("primaryGenreName"),
            year=year,
            publisher=item.get("collectionName"),
            url=item.get("trackViewUrl"),
        )
        return PortalProbe(key, label, candidate, "OK")

    def _search_audius(self, query: str) -> PortalProbe:
        key, label = "audius", "Audius"
        resp = self.session.get(
            "https://discoveryprovider.audius.co/v1/tracks/search",
            params={"query": query, "limit": "1"},
            timeout=self.timeout,
            headers={"User-Agent": self.user_agent},
        )
        if resp.status_code != 200:
            return PortalProbe(key, label, None, f"HTTP {resp.status_code}")
        payload = resp.json()
        results = payload.get("data", [])
        if not results:
            return PortalProbe(key, label, None, "Brak wyników")
        item = results[0]
        user = item.get("user") or {}
        date = str(item.get("release_date") or "")
        year = date[:4] if date[:4].isdigit() else None
        candidate = PortalCandidate(
            source_key=key,
            source_label=label,
            title=item.get("title"),
            artist=user.get("name"),
            genre=item.get("genre"),
            year=year,
            publisher=user.get("name"),
            url=item.get("permalink"),
        )
        return PortalProbe(key, label, candidate, "OK")

    def _search_archiveorg(self, query: str) -> PortalProbe:
        key, label = "archiveorg", "Internet Archive"
        resp = self.session.get(
            "https://archive.org/advancedsearch.php",
            params={
                "q": f"{query} AND mediatype:audio",
                "fl[]": "title,creator,date,identifier",
                "rows": "1",
                "page": "1",
                "output": "json",
            },
            timeout=self.timeout,
            headers={"User-Agent": self.user_agent},
        )
        if resp.status_code != 200:
            return PortalProbe(key, label, None, f"HTTP {resp.status_code}")
        payload = resp.json()
        docs = (((payload.get("response") or {}).get("docs")) or [])
        if not docs:
            return PortalProbe(key, label, None, "Brak wyników")
        item = docs[0]
        creator = item.get("creator")
        artist = creator[0] if isinstance(creator, list) and creator else creator
        date = str(item.get("date") or "")
        year = date[:4] if date[:4].isdigit() else None
        identifier = item.get("identifier")
        candidate = PortalCandidate(
            source_key=key,
            source_label=label,
            title=item.get("title"),
            artist=artist,
            year=year,
            url=f"https://archive.org/details/{identifier}" if identifier else None,
        )
        return PortalProbe(key, label, candidate, "OK")

    def _search_jiosaavn(self, query: str) -> PortalProbe:
        key, label = "jiosaavn", "JioSaavn"
        resp = self.session.get(
            "https://www.jiosaavn.com/api.php",
            params={
                "__call": "search.getResults",
                "q": query,
                "p": "1",
                "n": "1",
                "__api_version": "4",
                "_format": "json",
                "_marker": "0",
                "ctx": "web6dot0",
            },
            timeout=self.timeout,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        if resp.status_code != 200:
            return PortalProbe(key, label, None, f"HTTP {resp.status_code}")
        payload = resp.json()
        tracks = payload.get("results", [])
        if not tracks:
            return PortalProbe(key, label, None, "Brak wyników")
        item = tracks[0]
        candidate = PortalCandidate(
            source_key=key,
            source_label=label,
            title=item.get("song"),
            artist=item.get("primary_artists"),
            album=item.get("album"),
            year=str(item.get("year") or "") or None,
            publisher=item.get("music"),
            url=f"https://www.jiosaavn.com/song/{item.get('song')}/{item.get('id')}" if item.get("id") else None,
        )
        return PortalProbe(key, label, candidate, "OK")

    def _search_musicbrainz(self, query: str) -> PortalProbe:
        key, label = "musicbrainz_portal", "MusicBrainz"
        resp = self.session.get(
            "https://musicbrainz.org/ws/2/recording",
            params={"query": query, "fmt": "json", "limit": "1"},
            timeout=self.timeout,
            headers={"User-Agent": f"{self.musicbrainz_app_name}/1.0"},
        )
        if resp.status_code != 200:
            return PortalProbe(key, label, None, f"HTTP {resp.status_code}")
        payload = resp.json()
        items = payload.get("recordings", [])
        if not items:
            return PortalProbe(key, label, None, "Brak wyników")
        item = items[0]
        artist_credit = item.get("artist-credit", [])
        artist = None
        if artist_credit and isinstance(artist_credit[0], dict):
            artist = artist_credit[0].get("name")
        candidate = PortalCandidate(
            source_key=key,
            source_label=label,
            title=item.get("title"),
            artist=artist,
            url=f"https://musicbrainz.org/recording/{item.get('id')}" if item.get("id") else None,
        )
        return PortalProbe(key, label, candidate, "OK")

    def _search_discogs(self, query: str) -> PortalProbe:
        key, label = "discogs_portal", "Discogs"
        if not self.discogs_token:
            return PortalProbe(key, label, None, "Brak tokenu API")
        resp = self.session.get(
            "https://api.discogs.com/database/search",
            params={"q": query, "type": "release", "per_page": "1"},
            timeout=self.timeout,
            headers={
                "User-Agent": self.user_agent,
                "Authorization": f"Discogs token={self.discogs_token}",
            },
        )
        if resp.status_code != 200:
            return PortalProbe(key, label, None, f"HTTP {resp.status_code}")
        payload = resp.json()
        results = payload.get("results", [])
        if not results:
            return PortalProbe(key, label, None, "Brak wyników")
        item = results[0]
        raw_title = str(item.get("title") or "")
        artist, title = _split_artist_title(raw_title)
        genres = item.get("genre") or []
        labels = item.get("label") or []
        candidate = PortalCandidate(
            source_key=key,
            source_label=label,
            title=title or raw_title,
            artist=artist,
            genre=genres[0] if genres else None,
            year=str(item.get("year") or "") or None,
            publisher=labels[0] if labels else None,
            url=item.get("uri"),
        )
        return PortalProbe(key, label, candidate, "OK")

    def _discover_soundcloud_client_id(self) -> str | None:
        if self._SOUNDCLOUD_CLIENT_ID:
            return self._SOUNDCLOUD_CLIENT_ID
        try:
            home = self.session.get(
                "https://soundcloud.com",
                timeout=self.timeout,
                headers={"User-Agent": "Mozilla/5.0"},
            )
        except Exception:
            return None
        if home.status_code != 200:
            return None
        scripts = re.findall(r'<script[^>]+src="([^"]+)"', home.text)
        for src in scripts:
            if "sndcdn.com/assets/" not in src:
                continue
            script_url = src if src.startswith("http") else f"https://soundcloud.com{src}"
            try:
                script = self.session.get(script_url, timeout=self.timeout, headers={"User-Agent": "Mozilla/5.0"})
            except Exception:
                continue
            if script.status_code != 200:
                continue
            match = re.search(r'client_id\s*[:=]\s*"([a-zA-Z0-9]{20,})"', script.text)
            if not match:
                match = re.search(r'"client_id":"([a-zA-Z0-9]{20,})"', script.text)
            if match:
                self._SOUNDCLOUD_CLIENT_ID = match.group(1)
                return self._SOUNDCLOUD_CLIENT_ID
        return None


def _extract_between(text: str, start_marker: str, end_marker: str) -> str | None:
    start = text.find(start_marker)
    if start == -1:
        return None
    start += len(start_marker)
    end = text.find(end_marker, start)
    if end == -1:
        return None
    return text[start:end]


def _extract_after_regex(text: str, start_pattern: str, end_pattern: str) -> str | None:
    start = re.search(start_pattern, text, re.S)
    if not start:
        return None
    remainder = text[start.end() :]
    end = re.search(end_pattern, remainder, re.S)
    if not end:
        return None
    return remainder[: end.start()]


def _clean_html_text(text: str | None) -> str | None:
    if not text:
        return None
    cleaned = re.sub(r"<[^>]+>", " ", text)
    cleaned = unescape(cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned or None


def _split_artist_title(value: str | None) -> tuple[str | None, str | None]:
    if not value:
        return None, None
    if " - " in value:
        left, right = value.split(" - ", 1)
        return left.strip() or None, right.strip() or None
    return None, value.strip() or None


def _split_query(query: str) -> tuple[str, str]:
    """Rozdziela query na (artysta, tytuł) na podstawie separatora ' - '.

    Jeśli brak separatora, zwraca ("", query) — tytuł = cała fraza.
    """
    if " - " in query:
        left, right = query.split(" - ", 1)
        return left.strip(), right.strip()
    return "", query.strip()
