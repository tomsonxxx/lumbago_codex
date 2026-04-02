from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import html
import json
import re
from typing import Any
from copy import deepcopy

from lumbago_app.services.metadata_providers import MusicBrainzProvider
from lumbago_app.data.repository import get_metadata_cache, set_metadata_cache, list_tracks

import requests

from lumbago_app.core.models import Track
from lumbago_app.core.config import cache_dir
from lumbago_app.core.audio import extract_metadata, read_tags


@dataclass
class SourceProbe:
    key: str
    label: str
    status: str
    fields: list[str] = field(default_factory=list)
    detail: str = ""


@dataclass
class MetadataFillReport:
    method: str
    changed_fields: list[str] = field(default_factory=list)
    sources: list[SourceProbe] = field(default_factory=list)

    @property
    def summary(self) -> str:
        if self.changed_fields:
            return f"Zmiany: {', '.join(self.changed_fields)}"
        successful = [source.label for source in self.sources if source.status == "hit"]
        if successful:
            return f"Źródła bez zmian: {', '.join(successful)}"
        return "Brak nowych danych"


LOCAL_SOURCE_LABELS = {
    "file_tags": "Tagi pliku",
    "filename_pattern": "Wzorzec nazwy pliku",
    "folder_structure": "Struktura katalogow",
    "sidecar_json": "Plik sidecar JSON",
    "folder_json": "Plik folder.json / metadata.json",
    "cue_sheet": "Plik CUE",
    "local_library": "Biblioteka lokalna",
    "musicbrainz_search": "MusicBrainz Search",
    "musicbrainz_recording": "MusicBrainz Recording",
    "cover_art_archive": "Cover Art Archive",
    "portal_search_youtube": "YouTube Search",
    "portal_search_soundcloud": "SoundCloud Search",
    "portal_search_spotify": "Spotify Search",
    "portal_search_apple_music": "Apple Music Search",
    "portal_search_deezer": "Deezer Search",
    "portal_search_bandcamp": "Bandcamp Search",
    "portal_search_beatport": "Beatport Search",
    "portal_search_tidal": "TIDAL Search",
    "portal_search_amazon_music": "Amazon Music Search",
    "portal_search_lastfm": "Last.fm Search",
    "portal_search_traxsource": "Traxsource Search",
    "portal_search_junodownload": "Juno Download Search",
    "portal_search_audiomack": "Audiomack Search",
    "portal_consensus": "Konsensus zrodel online",
}
METHOD_CATALOG = {
    "offline": "Offline — pliki i baza lokalna",
    "online": "Online — MusicBrainz + publiczne portale",
    "mix": "Mix — wszystkie dostępne źródła",
}


SEARCHABLE_METADATA_FIELDS = [
    "title",
    "artist",
    "album",
    "albumartist",
    "year",  # date
    "genre",
    "tracknumber",
    "discnumber",
    "composer",
    "bpm",
    "key",
    "rating",
    "comment",
    "lyrics",
    "isrc",
    "publisher",
    "grouping",
    "copyright",
    "remixer",
    "mood",
    "energy",
]

SOURCE_WEIGHTS: dict[str, float] = {
    "file_tags": 1.00,
    "sidecar_json": 0.92,
    "folder_json": 0.90,
    "cue_sheet": 0.82,
    "local_library": 0.86,
    "musicbrainz_search": 0.94,
    "portal_search_spotify": 0.88,
    "portal_search_apple_music": 0.86,
    "portal_search_deezer": 0.84,
    "portal_search_tidal": 0.84,
    "portal_search_beatport": 0.84,
    "portal_search_bandcamp": 0.82,
    "portal_search_soundcloud": 0.80,
    "portal_search_youtube": 0.80,
    "portal_search_amazon_music": 0.79,
    "portal_search_lastfm": 0.78,
    "portal_search_traxsource": 0.78,
    "portal_search_junodownload": 0.76,
    "portal_search_audiomack": 0.76,
}


class MetadataEnricher:
    def __init__(
        self,
        musicbrainz_app: str | None,
        validation_policy: str | None = None,
        cache_ttl_days: int = 30,
    ):
        self.musicbrainz_app = musicbrainz_app or "LumbagoMusicAI"
        self.validation_policy = validation_policy or "balanced"
        self.cache_ttl_seconds = max(0, cache_ttl_days) * 24 * 3600

    def enrich_track(self, track: Track) -> Track | None:
        return self.enrich_from_musicbrainz_search(track)

    def enrich_from_musicbrainz_search(self, track: Track) -> Track | None:
        query = _build_text_query(track)
        if not query:
            return None
        provider = MusicBrainzProvider(self.musicbrainz_app)
        cache_key = f"musicbrainz:search:{query}"
        data = get_metadata_cache(cache_key, self.cache_ttl_seconds) or provider.search_recording(query)
        if data:
            set_metadata_cache(cache_key, data, source="musicbrainz")
        candidate = _select_musicbrainz_recording(data)
        if not candidate:
            return None
        if not _validate_candidate(
            track, candidate.get("title"), _first_artist(candidate), policy=self.validation_policy
        ):
            return None
        _apply_musicbrainz_metadata(track, candidate)
        # Fetch detailed recording to fill remaining fields (composer, tracknumber, etc.)
        recording_id = candidate.get("id")
        if recording_id:
            detailed = self._fetch_musicbrainz_recording(recording_id)
            if detailed:
                _apply_musicbrainz_metadata(track, detailed)
        return track

    def _fetch_musicbrainz_recording(self, recording_id: str) -> dict[str, Any] | None:
        cache_key = f"musicbrainz:recording:{recording_id}"
        cached = get_metadata_cache(cache_key, self.cache_ttl_seconds)
        if cached:
            return cached
        url = f"https://musicbrainz.org/ws/2/recording/{recording_id}"
        params = {"fmt": "json", "inc": "artists+releases+tags+isrcs+media+artist-rels+release-rels"}
        headers = {"User-Agent": f"{self.musicbrainz_app}/0.1 (local)"}
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            set_metadata_cache(cache_key, data, source="musicbrainz")
            return data
        except Exception:
            return None


def _apply_musicbrainz_metadata(track: Track, payload: dict[str, Any]) -> str | None:
    track.title = track.title or payload.get("title")
    artists = payload.get("artist-credit", [])
    if artists:
        names = [artist.get("name") for artist in artists if isinstance(artist, dict)]
        if names:
            track.artist = track.artist or ", ".join(names)
    # ISRC
    isrcs = payload.get("isrcs", [])
    if isrcs and isinstance(isrcs, list):
        track.isrc = track.isrc or isrcs[0]
    releases = payload.get("releases", [])
    release_id = None
    if releases:
        release = releases[0]
        album_candidate = release.get("title")
        if album_candidate and not _is_compilation_album(album_candidate):
            track.album = track.album or album_candidate
            release_id = release.get("id")
            release_date = release.get("date")
            release_year = _parse_year(release_date)
            if release_year and _is_valid_year(release_year):
                track.year = track.year or str(release_year)
        # Track number from release media
        media = release.get("media", [])
        if media:
            for medium in media:
                for mb_track in medium.get("tracks", medium.get("track-list", [])):
                    if mb_track.get("id") == payload.get("id") or mb_track.get("title") == payload.get("title"):
                        track.tracknumber = track.tracknumber or mb_track.get("number")
                        position = medium.get("position")
                        if position:
                            track.discnumber = track.discnumber or str(position)
                        break
        # Album artist from release artist-credit
        release_artists = release.get("artist-credit", [])
        if release_artists:
            ra_names = [a.get("name") for a in release_artists if isinstance(a, dict)]
            if ra_names:
                track.albumartist = track.albumartist or ", ".join(ra_names)
        label_info = release.get("label-info", [])
        if label_info and isinstance(label_info, list):
            first_label = label_info[0] if isinstance(label_info[0], dict) else {}
            label_name = None
            if isinstance(first_label, dict):
                label = first_label.get("label")
                if isinstance(label, dict):
                    label_name = label.get("name")
            if label_name:
                track.publisher = track.publisher or label_name
                track.copyright = track.copyright or label_name
    tags = payload.get("tags", [])
    if tags:
        top = max(tags, key=lambda item: item.get("count", 0))
        tag_name = top.get("name")
        if tag_name:
            track.genre = track.genre or tag_name
        mood_candidate = _pick_mood_from_tags(tags)
        if mood_candidate:
            track.mood = track.mood or mood_candidate
    relations = payload.get("relations", [])
    if relations and isinstance(relations, list):
        for relation in relations:
            if not isinstance(relation, dict):
                continue
            rel_type = str(relation.get("type", "")).strip().lower()
            artist_info = relation.get("artist")
            artist_name = artist_info.get("name") if isinstance(artist_info, dict) else None
            if rel_type == "composer" and artist_name:
                track.composer = track.composer or artist_name
            if rel_type in {"mix", "remixer"} and artist_name:
                track.remixer = track.remixer or artist_name
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
    artist = _shorten_query_text(_sanitize_search_text(track.artist or track.albumartist))
    title = _shorten_query_text(_sanitize_search_text(track.title))
    if artist and title:
        return f'artist:"{artist}" AND recording:"{title}"'
    if title:
        return f'recording:"{title}"'
    fallback = _shorten_query_text(_sanitize_search_text(Path(track.path).stem.replace("_", " ").replace(".", " ")))
    if fallback:
        return f'recording:"{fallback}"'
    return None


def _select_musicbrainz_recording(payload: dict[str, Any] | None) -> dict[str, Any] | None:
    if not payload:
        return None
    recordings = payload.get("recordings", [])
    if not recordings:
        return None
    return recordings[0]


def _select_recording_id(
    payload: dict[str, Any] | None,
    preferred_title: str | None = None,
    preferred_artist: str | None = None,
) -> str | None:
    if not payload:
        return None
    results = payload.get("results", [])
    if not results:
        return None

    preferred_title_norm = _normalize(preferred_title)
    preferred_artist_norm = _normalize(preferred_artist)
    best_id: str | None = None
    best_score = -1.0

    for result in results:
        if not isinstance(result, dict):
            continue
        result_score = float(result.get("score", 0.0) or 0.0)
        for recording in result.get("recordings", []) or []:
            if not isinstance(recording, dict):
                continue
            recording_id = recording.get("id")
            if not recording_id:
                continue
            title = _normalize(recording.get("title"))
            artist = _normalize(_first_artist(recording))

            similarity = 0.0
            if preferred_title_norm:
                similarity += _token_similarity(preferred_title_norm, title)
            if preferred_artist_norm:
                similarity += _token_similarity(preferred_artist_norm, artist)
            if preferred_title_norm and preferred_artist_norm:
                similarity /= 2.0

            score = (similarity * 0.75) + (result_score * 0.25)
            if score > best_score:
                best_score = score
                best_id = str(recording_id)

    if best_id:
        return best_id

    first = results[0] if isinstance(results[0], dict) else None
    if not first:
        return None
    recordings = first.get("recordings", [])
    if not recordings:
        return None
    first_recording = recordings[0] if isinstance(recordings[0], dict) else None
    if not first_recording:
        return None
    return first_recording.get("id")


def _first_artist(recording: dict[str, Any]) -> str | None:
    artists = recording.get("artist-credit", []) or recording.get("artists", [])
    if not artists:
        return None
    first = artists[0]
    if isinstance(first, dict):
        return first.get("name")
    return str(first)


def _is_compilation_album(name: str) -> bool:
    lowered = name.lower()
    keywords = [
        "greatest hits",
        "best of",
        "collection",
        "anthology",
        "essentials",
        "ultimate",
        "the hits",
    ]
    return any(keyword in lowered for keyword in keywords)


def _parse_year(value: str | None) -> int | None:
    if not value:
        return None
    try:
        return int(value.split("-", 1)[0])
    except ValueError:
        return None


def _is_valid_year(value: int) -> bool:
    current_year = datetime.now().year
    return 1900 <= value <= current_year + 1


def _pick_mood_from_tags(tags: list[dict[str, Any]]) -> str | None:
    mood_keywords = {
        "happy",
        "sad",
        "dark",
        "melancholic",
        "uplifting",
        "energetic",
        "chill",
        "aggressive",
        "romantic",
    }
    for item in sorted(tags, key=lambda entry: entry.get("count", 0), reverse=True):
        name = str(item.get("name", "")).strip().lower()
        if not name:
            continue
        if name in mood_keywords:
            return name
    return None


def _normalize(value: str | None) -> str:
    if not value:
        return ""
    return "".join(ch.lower() for ch in value if ch.isalnum() or ch.isspace()).strip()


STRICT_SCORE_MIN = 0.9
BALANCED_SCORE_MIN = 0.65
LENIENT_SCORE_MIN = 0.4


def _token_similarity(left: str, right: str) -> float:
    if not left or not right:
        return 0.0
    left_tokens = set(left.split())
    right_tokens = set(right.split())
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / len(left_tokens | right_tokens)


def _match_score(track: Track, title: str | None, artist: str | None) -> float:
    title_a = _normalize(track.title)
    title_b = _normalize(title)
    artist_a = _normalize(track.artist)
    artist_b = _normalize(artist)

    if not title_a and not artist_a:
        return 0.0

    title_score = _token_similarity(title_a, title_b) if title_a else (1.0 if title_b else 0.0)
    artist_score = _token_similarity(artist_a, artist_b) if artist_a else (1.0 if artist_b else 0.0)
    return (title_score + artist_score) / 2.0


def _validate_candidate(
    track: Track, title: str | None, artist: str | None, policy: str = "strict"
) -> bool:
    title_a = _normalize(track.title)
    title_b = _normalize(title)
    artist_a = _normalize(track.artist)
    artist_b = _normalize(artist)

    score = _match_score(track, title, artist)
    if policy == "strict":
        if title_a and title_b and title_a == title_b:
            if artist_a and artist_b and artist_a == artist_b:
                return True
        return score >= STRICT_SCORE_MIN
    if policy == "lenient":
        return score >= LENIENT_SCORE_MIN
    return score >= BALANCED_SCORE_MIN


class AutoMetadataFiller:
    def __init__(
        self,
        musicbrainz_app: str | None,
        validation_policy: str | None = None,
        cache_ttl_days: int = 30,
        source_workers: int = 6,
    ):
        self.musicbrainz_app = musicbrainz_app
        self.validation_policy = validation_policy or "balanced"
        self.cache_ttl_days = cache_ttl_days
        self.source_workers = max(1, min(12, int(source_workers)))
        self._library_snapshot: list[Track] | None = None

    def fill_missing(self, track: Track, method: str) -> Track | None:
        report = self.fill_missing_with_report(track, method)
        return track if report.changed_fields else None

    def fill_missing_with_report(self, track: Track, method: str) -> MetadataFillReport:
        enricher = MetadataEnricher(
            self.musicbrainz_app,
            validation_policy=self.validation_policy,
            cache_ttl_days=self.cache_ttl_days,
        )
        before = deepcopy(track)
        report = MetadataFillReport(method=method)

        # Legacy method aliases → map to new 3 methods
        legacy_map = {
            "auto": "mix", "local": "offline",
            "file_tags": "offline", "filename": "offline", "sidecar": "offline",
            "folder_json": "offline", "cue": "offline", "library": "offline",
            "musicbrainz": "online",
            "text_search": "online", "online_hybrid": "mix",
        }
        resolved = legacy_map.get(method, method)

        if resolved == "offline":
            self._run_local_sources(track, report)
            self._run_local_library_source(track, report)
        elif resolved == "online":
            self._run_online_pipeline(enricher, track, report)
        elif resolved == "mix":
            self._run_local_sources(track, report)
            self._run_local_library_source(track, report)
            self._run_online_pipeline(enricher, track, report)
            self._run_portal_search_sources(track, report)
        else:
            report.sources.append(SourceProbe(method, method, "miss", detail="Nieznana metoda"))

        report.changed_fields = _collect_changed_fields(before, track)
        return report

    def _run_local_sources(self, track: Track, report: MetadataFillReport) -> None:
        self._run_file_tag_source(track, report)
        self._run_sidecar_source(track, report)
        self._run_folder_json_source(track, report)
        self._run_cue_source(track, report)
        self._run_filename_folder_sources(track, report)

    def _run_file_tag_source(self, track: Track, report: MetadataFillReport) -> None:
        try:
            tags = read_tags(Path(track.path))
        except Exception as exc:
            report.sources.append(SourceProbe("file_tags", LOCAL_SOURCE_LABELS["file_tags"], "error", detail=str(exc)))
            return
        fields = _apply_mapping(track, tags, {
            "title": "title", "artist": "artist", "album": "album",
            "albumartist": "albumartist", "year": "year", "date": "year", "genre": "genre",
            "tracknumber": "tracknumber", "discnumber": "discnumber",
            "composer": "composer", "key": "key", "bpm": "bpm",
            "rating": "rating",
            "mood": "mood", "energy": "energy",
            "comment": "comment", "lyrics": "lyrics", "isrc": "isrc",
            "publisher": "publisher", "grouping": "grouping",
            "copyright": "copyright", "remixer": "remixer",
        })
        report.sources.append(SourceProbe("file_tags", LOCAL_SOURCE_LABELS["file_tags"], "hit" if fields else "miss", fields=fields, detail=f"{len(tags)} tagów odczytanych" if tags else "Brak tagów audio"))

    def _run_filename_folder_sources(self, track: Track, report: MetadataFillReport) -> None:
        before = deepcopy(track)
        refreshed = extract_metadata(Path(track.path))
        filename_fields = _collect_changed_fields(before, refreshed, allowed={"title", "artist"})
        for field_name in ("title", "artist"):
            value = getattr(refreshed, field_name)
            if value and not getattr(track, field_name):
                setattr(track, field_name, value)

        folder_before = deepcopy(track)
        for field_name in ("album", "artist"):
            value = getattr(refreshed, field_name)
            if value and not getattr(track, field_name):
                setattr(track, field_name, value)
        folder_fields = _collect_changed_fields(folder_before, track, allowed={"album", "artist"})

        report.sources.append(SourceProbe("filename_pattern", LOCAL_SOURCE_LABELS["filename_pattern"], "hit" if filename_fields else "miss", fields=filename_fields))
        report.sources.append(SourceProbe("folder_structure", LOCAL_SOURCE_LABELS["folder_structure"], "hit" if folder_fields else "miss", fields=folder_fields))

    def _run_sidecar_source(self, track: Track, report: MetadataFillReport) -> None:
        path = Path(track.path).with_suffix(".json")
        if not path.exists():
            report.sources.append(SourceProbe("sidecar_json", LOCAL_SOURCE_LABELS["sidecar_json"], "miss", detail="Brak pliku"))
            return
        refreshed = extract_metadata(Path(track.path))
        fields = _copy_missing_fields(track, refreshed, {
            "title", "artist", "album", "albumartist", "genre", "key", "mood", "energy", "bpm",
            "tracknumber", "discnumber", "composer", "rating", "comment", "lyrics",
            "isrc", "publisher", "grouping", "copyright", "remixer",
        })
        report.sources.append(SourceProbe("sidecar_json", LOCAL_SOURCE_LABELS["sidecar_json"], "hit" if fields else "miss", fields=fields, detail=str(path.name)))

    def _run_folder_json_source(self, track: Track, report: MetadataFillReport) -> None:
        folder = Path(track.path).parent
        json_path = next((folder / name for name in ("folder.json", "metadata.json") if (folder / name).exists()), None)
        if json_path is None:
            report.sources.append(SourceProbe("folder_json", LOCAL_SOURCE_LABELS["folder_json"], "miss", detail="Brak pliku"))
            return
        refreshed = extract_metadata(Path(track.path))
        fields = _copy_missing_fields(track, refreshed, {
            "album", "albumartist", "artist", "genre", "key", "mood", "energy", "bpm",
            "tracknumber", "discnumber", "composer", "rating", "comment", "lyrics",
            "publisher", "grouping", "copyright", "isrc", "remixer",
        })
        report.sources.append(SourceProbe("folder_json", LOCAL_SOURCE_LABELS["folder_json"], "hit" if fields else "miss", fields=fields, detail=str(json_path.name)))

    def _run_cue_source(self, track: Track, report: MetadataFillReport) -> None:
        file_path = Path(track.path)
        cue_path = file_path.with_suffix(".cue")
        if not cue_path.exists():
            album_cue = file_path.parent / "album.cue"
            cue_path = album_cue if album_cue.exists() else None
        if cue_path is None:
            report.sources.append(SourceProbe("cue_sheet", LOCAL_SOURCE_LABELS["cue_sheet"], "miss", detail="Brak pliku"))
            return
        refreshed = extract_metadata(file_path)
        fields = _copy_missing_fields(track, refreshed, {"title", "artist", "album"})
        report.sources.append(SourceProbe("cue_sheet", LOCAL_SOURCE_LABELS["cue_sheet"], "hit" if fields else "miss", fields=fields, detail=cue_path.name))

    def _run_local_library_source(self, track: Track, report: MetadataFillReport) -> None:
        target_title = _normalize(track.title)
        target_artist = _normalize(track.artist)
        if not target_title and not target_artist:
            report.sources.append(SourceProbe("local_library", LOCAL_SOURCE_LABELS["local_library"], "miss", detail="Brak klucza wyszukiwania"))
            return
        match = None
        for candidate in self._list_library_tracks():
            if candidate.path == track.path:
                continue
            if target_title and _normalize(candidate.title) != target_title:
                continue
            if target_artist and _normalize(candidate.artist) != target_artist:
                continue
            match = candidate
            break
        if match is None:
            report.sources.append(SourceProbe("local_library", LOCAL_SOURCE_LABELS["local_library"], "miss", detail="Brak dopasowania"))
            return
        fields = _copy_missing_fields(track, match, {
            "album", "albumartist", "genre", "year", "bpm", "key", "mood", "energy",
            "tracknumber", "discnumber", "composer", "rating", "comment", "lyrics",
            "isrc", "publisher", "grouping", "copyright", "remixer",
        })
        report.sources.append(SourceProbe("local_library", LOCAL_SOURCE_LABELS["local_library"], "hit" if fields else "miss", fields=fields, detail=Path(match.path).name))

    def _list_library_tracks(self) -> list[Track]:
        if self._library_snapshot is None:
            self._library_snapshot = list_tracks()
        return self._library_snapshot

    def _run_online_pipeline(
        self,
        enricher: MetadataEnricher,
        track: Track,
        report: MetadataFillReport,
        only: str | None = None,
    ) -> None:
        if only in {None, "musicbrainz"}:
            self._run_musicbrainz_source(enricher, track, report)
            if only == "musicbrainz":
                return

    def _run_musicbrainz_source(self, enricher: MetadataEnricher, track: Track, report: MetadataFillReport) -> None:
        before = deepcopy(track)
        enriched = enricher.enrich_from_musicbrainz_search(track)
        fields = _collect_changed_fields(before, track)
        report.sources.append(SourceProbe("musicbrainz_search", LOCAL_SOURCE_LABELS["musicbrainz_search"], "hit" if enriched and fields else "miss", fields=fields))

    def _run_portal_search_sources(self, track: Track, report: MetadataFillReport) -> None:
        queries = _build_portal_queries(track)
        if not queries:
            for portal in _PORTAL_SOURCES:
                report.sources.append(
                    SourceProbe(portal.key, portal.label, "miss", detail="Brak klucza wyszukiwania")
                )
            return

        hits: list[tuple[str, dict[str, str], str, int]] = []
        scanned: list[tuple[PortalSource, dict[str, str] | None, int, str]] = []

        max_workers = min(self.source_workers, len(_PORTAL_SOURCES))
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            future_map = {
                pool.submit(_search_public_portal_candidate, track, portal.key, queries): portal
                for portal in _PORTAL_SOURCES
            }
            for future in as_completed(future_map):
                portal = future_map[future]
                try:
                    candidate, result_count, query_used = future.result()
                except Exception:
                    candidate, result_count, query_used = None, 0, "blad wyszukiwania"
                scanned.append((portal, candidate, result_count, query_used))

        scanned.sort(key=lambda item: item[0].priority)
        for portal, candidate, result_count, query_used in scanned:
            if candidate is not None:
                hits.append((portal.key, candidate, query_used, result_count))
            report.sources.append(
                SourceProbe(
                    portal.key,
                    portal.label,
                    "hit" if candidate is not None else "miss",
                    fields=[],
                    detail=f"Wyniki: {result_count}; zapytanie: {query_used}",
                )
            )

        if not hits:
            report.sources.append(
                SourceProbe("portal_consensus", LOCAL_SOURCE_LABELS["portal_consensus"], "miss", detail="Brak dopasowan")
            )
            return

        before = deepcopy(track)
        best_candidate, detail = _build_portal_consensus(track, hits)
        if best_candidate is not None:
            _apply_portal_candidate(track, best_candidate)
        fields = _collect_changed_fields(before, track)
        report.sources.append(
            SourceProbe(
                "portal_consensus",
                LOCAL_SOURCE_LABELS["portal_consensus"],
                "hit" if fields else "miss",
                fields=fields,
                detail=detail,
            )
        )


def available_metadata_methods() -> dict[str, str]:
    return dict(METHOD_CATALOG)


def _copy_missing_fields(target: Track, source: Track, allowed: set[str]) -> list[str]:
    changed: list[str] = []
    for field_name in allowed:
        source_value = getattr(source, field_name, None)
        target_value = getattr(target, field_name, None)
        if _has_field_value(field_name, source_value) and not _has_field_value(field_name, target_value):
            setattr(target, field_name, _normalize_field_value(field_name, source_value))
            changed.append(field_name)
    return sorted(changed)


def _apply_mapping(target: Track, payload: dict[str, Any], field_map: dict[str, str]) -> list[str]:
    changed: list[str] = []
    for source_key, field_name in field_map.items():
        value = payload.get(source_key)
        if not _has_field_value(field_name, value):
            continue
        if _has_field_value(field_name, getattr(target, field_name, None)):
            continue
        setattr(target, field_name, _normalize_field_value(field_name, value))
        changed.append(field_name)
    return sorted(changed)


def _has_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        normalized = value.strip().lower()
        if not normalized:
            return False
        return normalized not in {"-", "—", "\\", "/", "unknown", "n/a", "none", "null", "brak"}
    return True


_ALL_METADATA_FIELDS = {
    "title", "artist", "album", "albumartist", "year", "genre",
    "tracknumber", "discnumber", "composer",
    "bpm", "key", "rating", "mood", "energy",
    "comment", "lyrics", "isrc", "publisher", "grouping", "copyright", "remixer",
    "artwork_path",
}


def _collect_changed_fields(before: Track, after: Track, allowed: set[str] | None = None) -> list[str]:
    fields = allowed or _ALL_METADATA_FIELDS
    changed: list[str] = []
    for field_name in fields:
        if getattr(before, field_name, None) != getattr(after, field_name, None):
            changed.append(field_name)
    return sorted(changed)


@dataclass(frozen=True)
class PortalSource:
    key: str
    label: str
    site_query: str
    domain_hint: str
    priority: int


_PORTAL_SOURCES: list[PortalSource] = [
    PortalSource("portal_search_spotify", LOCAL_SOURCE_LABELS["portal_search_spotify"], "site:open.spotify.com/track", "open.spotify.com/track/", 1),
    PortalSource("portal_search_apple_music", LOCAL_SOURCE_LABELS["portal_search_apple_music"], "site:music.apple.com song", "music.apple.com/", 2),
    PortalSource("portal_search_deezer", LOCAL_SOURCE_LABELS["portal_search_deezer"], "site:deezer.com/track", "deezer.com/track/", 3),
    PortalSource("portal_search_soundcloud", LOCAL_SOURCE_LABELS["portal_search_soundcloud"], "site:soundcloud.com", "soundcloud.com/", 4),
    PortalSource("portal_search_youtube", LOCAL_SOURCE_LABELS["portal_search_youtube"], "site:youtube.com/watch", "youtube.com/watch", 5),
    PortalSource("portal_search_bandcamp", LOCAL_SOURCE_LABELS["portal_search_bandcamp"], "site:bandcamp.com/track", "bandcamp.com/track/", 6),
    PortalSource("portal_search_beatport", LOCAL_SOURCE_LABELS["portal_search_beatport"], "site:beatport.com/track", "beatport.com/track/", 7),
    PortalSource("portal_search_tidal", LOCAL_SOURCE_LABELS["portal_search_tidal"], "site:tidal.com/browse/track", "tidal.com/browse/track/", 8),
    PortalSource("portal_search_amazon_music", LOCAL_SOURCE_LABELS["portal_search_amazon_music"], "site:music.amazon.com/tracks", "music.amazon.com/tracks/", 9),
    PortalSource("portal_search_lastfm", LOCAL_SOURCE_LABELS["portal_search_lastfm"], "site:last.fm/music", "last.fm/music/", 10),
    PortalSource("portal_search_traxsource", LOCAL_SOURCE_LABELS["portal_search_traxsource"], "site:traxsource.com/track", "traxsource.com/track/", 11),
    PortalSource("portal_search_junodownload", LOCAL_SOURCE_LABELS["portal_search_junodownload"], "site:junodownload.com products", "junodownload.com", 12),
    PortalSource("portal_search_audiomack", LOCAL_SOURCE_LABELS["portal_search_audiomack"], "site:audiomack.com", "audiomack.com/", 13),
]
_PORTAL_SOURCE_MAP = {portal.key: portal for portal in _PORTAL_SOURCES}

_PORTAL_SUFFIX_CLEAN = [
    " - youtube",
    " | youtube",
    " - spotify",
    " | spotify",
    " - soundcloud",
    " | soundcloud",
    " - apple music",
    " | apple music",
    " - deezer",
    " | deezer",
    " - beatport",
    " | beatport",
    " - tidal",
    " | tidal",
    " - traxsource",
    " | traxsource",
    " - bandcamp",
    " | bandcamp",
    " - audiomack",
    " | audiomack",
    " - last.fm",
    " | last.fm",
]
_QUERY_STOP_WORDS = {
    "official", "video", "audio", "lyrics", "lyric", "hq", "hd", "4k", "8k",
    "remaster", "remastered", "live", "version", "edit", "mix",
}
_MAX_PORTAL_QUERIES = 2

_RESULT_TITLE_RE = re.compile(r'<a[^>]*class="[^"]*result__a[^"]*"[^>]*>(.*?)</a>', re.IGNORECASE | re.DOTALL)
_TAG_RE = re.compile(r"<[^>]+>")
_MARKDOWN_HEADING_LINK_RE = re.compile(r"##\s+\[(?P<title>[^\]]+)\]\((?P<url>https?://[^)]+)\)")
_MARKDOWN_INLINE_LINK_RE = re.compile(r"\[(?P<label>[^\]]+)\]\((?P<url>https?://[^)]+)\)")
_PORTAL_SEARCH_CACHE: dict[str, str] = {}


def _build_portal_queries(track: Track) -> list[str]:
    artist = _sanitize_search_text(track.artist)
    title = _sanitize_search_text(track.title)
    stem = _sanitize_search_text(Path(track.path).stem.replace("_", " ").replace(".", " "))
    context = _build_search_context(track)

    candidates = [
        _shorten_query_text(f"{artist} {title}".strip()),
        _shorten_query_text(title),
        _shorten_query_text(f"{artist} {stem}".strip()),
        _shorten_query_text(stem),
        _shorten_query_text(context),
    ]
    unique: list[str] = []
    for query in candidates:
        normalized = " ".join(query.split()).strip()
        if not normalized:
            continue
        if normalized in unique:
            continue
        unique.append(normalized)
    return unique[:3]


def _build_search_context(track: Track) -> str:
    parts: list[str] = []
    for field_name in SEARCHABLE_METADATA_FIELDS:
        value = getattr(track, field_name, None)
        if not _has_field_value(field_name, value):
            continue
        if field_name == "year":
            parts.append(str(value))
            continue
        if field_name == "tracknumber":
            parts.append(f"track {value}")
            continue
        if field_name == "discnumber":
            parts.append(f"disc {value}")
            continue
        parts.append(str(value))
    return " ".join(parts)


def _sanitize_search_text(value: str | None) -> str:
    if not value:
        return ""
    text = str(value)
    text = re.sub(r"\[[^\]]*\]", " ", text)
    text = re.sub(r"\((official|lyric|audio|video|hq|hd|4k|8k|remaster|live)[^)]*\)", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\b(official|lyrics?|lyric|video|audio)\b", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"[^\w\s\-]", " ", text, flags=re.UNICODE)
    text = re.sub(r"\s+", " ", text)
    return text.strip(" -_")


def _shorten_query_text(value: str, max_tokens: int = 10, max_chars: int = 90) -> str:
    if not value:
        return ""
    raw_tokens = [token.strip() for token in value.split() if token.strip()]
    tokens: list[str] = []
    for token in raw_tokens:
        lowered = token.lower()
        if lowered in _QUERY_STOP_WORDS:
            continue
        tokens.append(token)
    if not tokens:
        tokens = raw_tokens
    trimmed = " ".join(tokens[:max_tokens]).strip()
    if len(trimmed) > max_chars:
        trimmed = trimmed[:max_chars].rsplit(" ", 1)[0].strip()
    return trimmed


def _search_public_portal_candidate(
    track: Track, portal_key: str, queries: list[str]
) -> tuple[dict[str, str] | None, int, str]:
    if not queries:
        return None, 0, "—"

    portal = _PORTAL_SOURCE_MAP.get(portal_key)
    if portal is None:
        return None, 0, "—"

    if portal_key == "portal_search_youtube":
        for query in queries[:_MAX_PORTAL_QUERIES]:
            youtube_candidate = _search_youtube_direct_candidate(track, query)
            if youtube_candidate is not None:
                return youtube_candidate, 1, query

    best_count = 0
    best_query = queries[0]
    best_candidate: dict[str, str] | None = None
    best_score = 0.0
    for query in queries[:_MAX_PORTAL_QUERIES]:
        search_query = f"{portal.site_query} {query}"
        markdown_text = _fetch_portal_search_markdown(search_query)
        titles = _extract_result_titles_from_markdown(markdown_text, portal.domain_hint)
        if titles:
            best_query = query
        best_count = max(best_count, len(titles))
        for title in titles:
            candidate = _parse_portal_candidate_from_title(title, portal_key)
            if candidate is None:
                continue
            score = _candidate_score(track, candidate, portal_key)
            if score > best_score:
                best_score = score
                best_candidate = candidate
            if score >= 0.72:
                return candidate, len(titles), query

        # Legacy fallback parser for classic DDG HTML.
        try:
            response = requests.get(
                "https://duckduckgo.com/html/",
                params={"q": search_query},
                headers={"User-Agent": "LumbagoMusicAI/0.1"},
                timeout=10,
            )
            response.raise_for_status()
            html_titles = _extract_result_titles(response.text)
        except Exception:
            html_titles = []
        best_count = max(best_count, len(html_titles))
        for title in html_titles:
            candidate = _parse_portal_candidate_from_title(title, portal_key)
            if candidate is None:
                continue
            score = _candidate_score(track, candidate, portal_key)
            if score > best_score:
                best_score = score
                best_candidate = candidate
    return best_candidate, best_count, best_query


def _candidate_score(track: Track, candidate: dict[str, str], source_key: str) -> float:
    value_score = _match_score(track, candidate.get("title"), candidate.get("artist"))
    source_score = SOURCE_WEIGHTS.get(source_key, 0.7)
    return (value_score * 0.75) + (source_score * 0.25)


def _fetch_portal_search_markdown(search_query: str) -> str:
    if search_query in _PORTAL_SEARCH_CACHE:
        return _PORTAL_SEARCH_CACHE[search_query]
    encoded = requests.utils.quote(search_query, safe="")
    url = f"https://r.jina.ai/http://duckduckgo.com/?q={encoded}"
    try:
        response = requests.get(url, headers={"User-Agent": "LumbagoMusicAI/0.1"}, timeout=12)
        response.raise_for_status()
        payload = response.text
    except Exception:
        payload = ""
    _PORTAL_SEARCH_CACHE[search_query] = payload
    return payload


def _extract_result_titles_from_markdown(markdown_text: str, domain_hint: str) -> list[str]:
    if not markdown_text or not domain_hint:
        return []

    titles: list[str] = []
    for match in _MARKDOWN_HEADING_LINK_RE.finditer(markdown_text):
        url = match.group("url").strip().lower()
        title = match.group("title").strip()
        if domain_hint not in url:
            continue
        if title:
            titles.append(title)

    if titles:
        return titles

    # Fallback: inline links without heading marker.
    for match in _MARKDOWN_INLINE_LINK_RE.finditer(markdown_text):
        url = match.group("url").strip().lower()
        label = match.group("label").strip()
        if domain_hint not in url:
            continue
        if label and "http" not in label.lower():
            titles.append(label)
    return titles


def _extract_result_titles(html_text: str) -> list[str]:
    results: list[str] = []
    for raw_title in _RESULT_TITLE_RE.findall(html_text):
        no_tags = _TAG_RE.sub("", raw_title)
        clean = html.unescape(no_tags).strip()
        if clean:
            results.append(clean)
    return results


def _parse_portal_candidate_from_title(result_title: str, portal_key: str) -> dict[str, str] | None:
    clean_title = _cleanup_portal_title(result_title)
    if not clean_title:
        return None

    match_by = re.match(r"^(?P<title>.+?)\s+by\s+(?P<artist>.+?)(?:\s+\||$)", clean_title, re.IGNORECASE)
    if match_by:
        parsed_title = match_by.group("title").strip()
        parsed_artist = match_by.group("artist").strip()
        if parsed_title and parsed_artist:
            return {"title": parsed_title, "artist": parsed_artist}

    match_dash = re.match(r"^(?P<artist>.+?)\s+-\s+(?P<title>.+)$", clean_title)
    if match_dash:
        parsed_artist = match_dash.group("artist").strip()
        parsed_title = match_dash.group("title").strip()
        if parsed_artist and parsed_title:
            return {"artist": parsed_artist, "title": parsed_title}

    # Apple Music / Deezer / Tidal pages often include "Song - Artist - Album".
    parts = [part.strip() for part in clean_title.split(" - ") if part.strip()]
    if len(parts) >= 3 and portal_key in {
        "portal_search_spotify",
        "portal_search_apple_music",
        "portal_search_deezer",
        "portal_search_tidal",
        "portal_search_amazon_music",
    }:
        return {"title": parts[0], "artist": parts[1], "album": parts[2]}

    return {"title": clean_title}


def _cleanup_portal_title(value: str) -> str:
    cleaned = _sanitize_search_text(value.strip())
    lowered = cleaned.lower()
    for suffix in _PORTAL_SUFFIX_CLEAN:
        if lowered.endswith(suffix):
            cleaned = cleaned[: -len(suffix)].strip()
            lowered = cleaned.lower()
    cleaned = re.sub(r"\s+\|\s+.*$", "", cleaned).strip()
    return cleaned


def _build_portal_consensus(
    track: Track,
    hits: list[tuple[str, dict[str, str], str, int]],
) -> tuple[dict[str, str] | None, str]:
    if not hits:
        return None, "Brak kandydatow do glosowania"

    vote_bucket: dict[str, dict[str, float]] = defaultdict(dict)
    for source_key, candidate, _query, _count in hits:
        source_weight = SOURCE_WEIGHTS.get(source_key, 0.7)
        for field_name in ("title", "artist", "album", "genre", "year", "mood", "isrc"):
            value = candidate.get(field_name)
            normalized = _normalize_vote_text(value)
            if not normalized:
                continue
            current = vote_bucket[field_name].get(normalized, 0.0)
            vote_bucket[field_name][normalized] = current + source_weight

    resolved: dict[str, str] = {}
    for field_name, weighted_values in vote_bucket.items():
        if not weighted_values:
            continue
        winner = max(weighted_values.items(), key=lambda item: item[1])[0]
        if winner:
            resolved[field_name] = winner

    if not resolved:
        return None, "Brak rozstrzygniecia w glosowaniu"

    detail_parts = [f"{field_name}:{value}" for field_name, value in sorted(resolved.items())]
    return resolved, f"Glosowanie ({len(hits)} zrodel): " + ", ".join(detail_parts)


def _has_strong_portal_consensus(hits: list[tuple[str, dict[str, str], str, int]]) -> bool:
    if len(hits) < 3:
        return False
    combo_weights: dict[str, float] = defaultdict(float)
    for source_key, candidate, _query, _count in hits:
        artist = _normalize_vote_text(candidate.get("artist"))
        title = _normalize_vote_text(candidate.get("title"))
        if not title:
            continue
        combo_key = f"{artist}::{title}"
        combo_weights[combo_key] += SOURCE_WEIGHTS.get(source_key, 0.7)
    if not combo_weights:
        return False
    top_weight = max(combo_weights.values())
    return top_weight >= 2.5


def _normalize_vote_text(value: str | None) -> str:
    if not value:
        return ""
    text = _sanitize_search_text(value)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _apply_portal_candidate(track: Track, candidate: dict[str, str]) -> None:
    candidate_title = candidate.get("title")
    if candidate_title and not _has_value(track.title):
        track.title = candidate_title
    elif candidate_title and _has_value(track.title) and _should_replace_noisy_title(str(track.title), candidate_title):
        track.title = candidate_title

    if candidate.get("artist") and not _has_value(track.artist):
        track.artist = candidate["artist"]
    if candidate.get("artist") and not _has_value(track.albumartist):
        track.albumartist = candidate["artist"]
    if candidate.get("album") and not _has_value(track.album):
        track.album = candidate["album"]
    if candidate.get("genre") and not _has_value(track.genre):
        track.genre = candidate["genre"]
    if candidate.get("mood") and not _has_value(track.mood):
        track.mood = candidate["mood"]

    remixer = _extract_remixer_name(candidate_title) or _extract_remixer_name(track.title)
    if remixer and not _has_value(track.remixer):
        track.remixer = remixer


def _search_youtube_direct_candidate(track: Track, query: str) -> dict[str, str] | None:
    try:
        response = requests.get(
            "https://www.youtube.com/results",
            params={"search_query": query},
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
            timeout=15,
        )
        response.raise_for_status()
    except Exception:
        return None

    payload = _extract_youtube_initial_data(response.text)
    if payload is None:
        return None

    for node in _walk_nodes(payload):
        if not isinstance(node, dict) or "videoRenderer" not in node:
            continue
        video = node.get("videoRenderer") or {}
        title = _youtube_text(video.get("title"))
        artist = _youtube_text(video.get("ownerText")) or _youtube_text(video.get("longBylineText"))
        if not title:
            continue
        candidate = _parse_portal_candidate_from_title(title, "portal_search_youtube") or {"title": title}
        if artist and not candidate.get("artist"):
            candidate["artist"] = artist
        if _validate_candidate(
            track,
            candidate.get("title"),
            candidate.get("artist"),
            policy="lenient",
        ):
            return candidate
    return None


def _extract_youtube_initial_data(page_html: str) -> dict[str, Any] | None:
    match = re.search(r"var ytInitialData = (\{.*?\});</script>", page_html, re.DOTALL)
    if not match:
        return None
    raw = match.group(1)
    try:
        return json.loads(raw)
    except Exception:
        return None


def _walk_nodes(value: Any):
    if isinstance(value, dict):
        yield value
        for nested in value.values():
            yield from _walk_nodes(nested)
    elif isinstance(value, list):
        for item in value:
            yield from _walk_nodes(item)


def _youtube_text(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, dict):
        if "simpleText" in value and isinstance(value["simpleText"], str):
            return value["simpleText"]
        runs = value.get("runs")
        if isinstance(runs, list):
            parts = [str(item.get("text", "")).strip() for item in runs if isinstance(item, dict)]
            text = "".join(parts).strip()
            return text or None
    return None


def _should_replace_noisy_title(current_title: str, candidate_title: str) -> bool:
    current = current_title.strip()
    candidate = candidate_title.strip()
    if not current or not candidate:
        return False
    if current == candidate:
        return False
    if not _looks_like_video_noise(current):
        return False
    if len(candidate) >= len(current):
        return False
    return True


def _has_field_value(field_name: str, value: Any) -> bool:
    if field_name == "rating":
        parsed = _parse_rating(value)
        return parsed is not None and parsed > 0
    return _has_value(value)


def _normalize_field_value(field_name: str, value: Any) -> Any:
    if field_name == "rating":
        return _parse_rating(value) or 0
    return value


def _parse_rating(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        rating = int(value)
        return rating if 0 <= rating <= 5 else None
    text = str(value).strip()
    if not text:
        return None
    if "/" in text:
        text = text.split("/", 1)[0].strip()
    match = re.search(r"\d+", text)
    if not match:
        return None
    rating = int(match.group(0))
    if rating > 5:
        # Common 10-star scale -> convert to 0..5.
        rating = max(0, min(5, round(rating / 2)))
    return rating if 0 <= rating <= 5 else None


def _looks_like_video_noise(title: str) -> bool:
    lowered = title.lower()
    markers = [
        "[official video]",
        "(official video)",
        "[official audio]",
        "(official audio)",
        "[lyric video]",
        "(lyric video)",
        "[visualizer]",
        "(visualizer)",
        "[audio]",
        "(audio)",
        "[4k",
        "[8k",
        "remastered",
        "official music video",
    ]
    return any(marker in lowered for marker in markers)


def _extract_remixer_name(title: str | None) -> str | None:
    if not title:
        return None
    match = re.search(r"\((?P<name>[^()]{2,60}?)\s+remix\)", title, re.IGNORECASE)
    if not match:
        return None
    raw = match.group("name").strip(" -_/")
    return raw or None

