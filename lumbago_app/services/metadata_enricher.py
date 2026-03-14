from __future__ import annotations

from pathlib import Path
import hashlib
from typing import Any

from lumbago_app.services.metadata_providers import DiscogsProvider, MusicBrainzProvider

import requests

from lumbago_app.core.models import Track
from lumbago_app.core.config import cache_dir
from lumbago_app.services.recognizer import AcoustIdRecognizer


class MetadataEnricher:
    def __init__(self, acoustid_key: str | None, musicbrainz_app: str | None):
        self.recognizer = AcoustIdRecognizer(acoustid_key)
        self.musicbrainz_app = musicbrainz_app or "LumbagoMusicAI"

    def enrich_track(self, track: Track) -> Track | None:
        result = self.recognizer.recognize(Path(track.path))
        if not result:
            return None
        recording_id = _select_recording_id(result)
        if not recording_id:
            return None
        metadata = self._fetch_musicbrainz_recording(recording_id)
        if not metadata:
            return None
        release_id = _apply_musicbrainz_metadata(track, metadata)
        if release_id:
            cover_path = _fetch_cover_art(release_id, track.path)
            if cover_path:
                track.artwork_path = str(cover_path)
        return track

    def enrich_from_musicbrainz_search(self, track: Track) -> Track | None:
        query = _build_text_query(track)
        if not query:
            return None
        provider = MusicBrainzProvider(self.musicbrainz_app)
        data = provider.search_recording(query)
        candidate = _select_musicbrainz_recording(data)
        if not candidate:
            return None
        if not _validate_candidate(track, candidate.get("title"), _first_artist(candidate)):
            return None
        track.title = track.title or candidate.get("title")
        track.artist = track.artist or _first_artist(candidate)
        return track

    def enrich_from_discogs_search(self, track: Track, token: str | None) -> Track | None:
        if not token:
            return None
        query = _build_text_query(track)
        if not query:
            return None
        provider = DiscogsProvider(token)
        data = provider.search_release(query)
        candidate = _select_discogs_release(data)
        if not candidate:
            return None
        if not _validate_candidate(track, candidate.get("title"), candidate.get("artist")):
            return None
        track.title = track.title or candidate.get("title")
        track.artist = track.artist or candidate.get("artist")
        track.genre = track.genre or candidate.get("genre")
        track.album = track.album or candidate.get("album")
        return track

    def _fetch_musicbrainz_recording(self, recording_id: str) -> dict[str, Any] | None:
        url = f"https://musicbrainz.org/ws/2/recording/{recording_id}"
        params = {"fmt": "json", "inc": "artists+releases+tags"}
        headers = {"User-Agent": f"{self.musicbrainz_app}/0.1 (local)"}
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=15)
            resp.raise_for_status()
            return resp.json()
        except Exception:
            return None


def _select_recording_id(payload: dict[str, Any]) -> str | None:
    results = payload.get("results", [])
    if not results:
        return None
    best = results[0]
    recordings = best.get("recordings", [])
    if not recordings:
        return None
    recording = recordings[0]
    return recording.get("id")


def _apply_musicbrainz_metadata(track: Track, payload: dict[str, Any]) -> str | None:
    track.title = track.title or payload.get("title")
    artists = payload.get("artist-credit", [])
    if artists:
        names = [artist.get("name") for artist in artists if isinstance(artist, dict)]
        if names:
            track.artist = track.artist or ", ".join(names)
    releases = payload.get("releases", [])
    release_id = None
    if releases:
        track.album = track.album or releases[0].get("title")
        release_id = releases[0].get("id")
    tags = payload.get("tags", [])
    if tags:
        top = max(tags, key=lambda item: item.get("count", 0))
        tag_name = top.get("name")
        if tag_name:
            track.genre = track.genre or tag_name
    return release_id


def _fetch_cover_art(release_id: str, track_path: str) -> Path | None:
    safe_hash = hashlib.sha1(track_path.encode("utf-8", errors="ignore")).hexdigest()
    target = cache_dir() / f"cover_{safe_hash}.jpg"
    if target.exists():
        return target
    url = f"https://coverartarchive.org/release/{release_id}/front-250"
    try:
        resp = requests.get(url, timeout=15)
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        target.write_bytes(resp.content)
        return target
    except Exception:
        return None


def _build_text_query(track: Track) -> str | None:
    if track.artist and track.title:
        return f'artist:"{track.artist}" AND recording:"{track.title}"'
    if track.title:
        return f'recording:"{track.title}"'
    return None


def _select_musicbrainz_recording(payload: dict[str, Any] | None) -> dict[str, Any] | None:
    if not payload:
        return None
    recordings = payload.get("recordings", [])
    if not recordings:
        return None
    return recordings[0]


def _first_artist(recording: dict[str, Any]) -> str | None:
    artists = recording.get("artist-credit", []) or recording.get("artists", [])
    if not artists:
        return None
    first = artists[0]
    if isinstance(first, dict):
        return first.get("name")
    return str(first)


def _select_discogs_release(payload: dict[str, Any] | None) -> dict[str, Any] | None:
    if not payload:
        return None
    results = payload.get("results", [])
    if not results:
        return None
    result = results[0]
    title = result.get("title")
    if not title:
        return None
    artist = None
    album = None
    if " - " in title:
        artist, album = [p.strip() for p in title.split(" - ", 1)]
    return {
        "title": album or title,
        "artist": artist,
        "genre": (result.get("genre") or [None])[0],
        "album": album,
    }


def _normalize(value: str | None) -> str:
    if not value:
        return ""
    return "".join(ch.lower() for ch in value if ch.isalnum() or ch.isspace()).strip()


def _validate_candidate(track: Track, title: str | None, artist: str | None) -> bool:
    title_a = _normalize(track.title)
    title_b = _normalize(title)
    artist_a = _normalize(track.artist)
    artist_b = _normalize(artist)
    if title_a and title_b and title_a not in title_b and title_b not in title_a:
        return False
    if artist_a and artist_b and artist_a not in artist_b and artist_b not in artist_a:
        return False
    return True


class AutoMetadataFiller:
    def __init__(self, acoustid_key: str | None, musicbrainz_app: str | None, discogs_token: str | None):
        self.acoustid_key = acoustid_key
        self.musicbrainz_app = musicbrainz_app
        self.discogs_token = discogs_token

    def fill_missing(self, track: Track, method: str) -> Track | None:
        enricher = MetadataEnricher(self.acoustid_key, self.musicbrainz_app)
        if method == "acoustid":
            return enricher.enrich_track(track)
        if method == "musicbrainz":
            return enricher.enrich_from_musicbrainz_search(track)
        if method == "discogs":
            return enricher.enrich_from_discogs_search(track, self.discogs_token)
        return None
