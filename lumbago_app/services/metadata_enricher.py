from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime
import hashlib
from typing import Any
from copy import deepcopy

from lumbago_app.services.metadata_providers import DiscogsProvider, MusicBrainzProvider
from lumbago_app.data.repository import get_metadata_cache, set_metadata_cache, list_tracks

import requests

from lumbago_app.core.models import Track
from lumbago_app.core.config import cache_dir
from lumbago_app.services.recognizer import AcoustIdRecognizer
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
    "folder_structure": "Struktura katalogów",
    "sidecar_json": "Plik sidecar JSON",
    "folder_json": "Plik folder.json / metadata.json",
    "cue_sheet": "Plik CUE",
    "local_library": "Biblioteka lokalna",
    "acoustid": "AcoustID",
    "musicbrainz_search": "MusicBrainz Search",
    "musicbrainz_recording": "MusicBrainz Recording",
    "discogs_search": "Discogs Search",
    "cover_art_archive": "Cover Art Archive",
}


METHOD_CATALOG = {
    "offline": "Offline — pliki i baza lokalna",
    "online": "Online — AcoustID, MusicBrainz, Discogs",
    "mix": "Mix — wszystkie dostępne źródła",
}


class MetadataEnricher:
    def __init__(
        self,
        acoustid_key: str | None,
        musicbrainz_app: str | None,
        validation_policy: str | None = None,
        cache_ttl_days: int = 30,
    ):
        self.recognizer = AcoustIdRecognizer(acoustid_key)
        self.musicbrainz_app = musicbrainz_app or "LumbagoMusicAI"
        self.validation_policy = validation_policy or "balanced"
        self.cache_ttl_seconds = max(0, cache_ttl_days) * 24 * 3600

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
        candidate_title = metadata.get("title")
        candidate_artist = _first_artist(metadata)
        if not _validate_candidate(track, candidate_title, candidate_artist, policy=self.validation_policy):
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
        track.title = track.title or candidate.get("title")
        track.artist = track.artist or _first_artist(candidate)
        # Extract ISRC from search results
        isrcs = candidate.get("isrcs", [])
        if isrcs and isinstance(isrcs, list):
            track.isrc = track.isrc or isrcs[0]
        return track

    def enrich_from_discogs_search(self, track: Track, token: str | None) -> Track | None:
        if not token:
            return None
        query = _build_text_query(track)
        if not query:
            return None
        provider = DiscogsProvider(token)
        cache_key = f"discogs:search:{query}"
        data = get_metadata_cache(cache_key, self.cache_ttl_seconds) or provider.search_release(query)
        if data:
            set_metadata_cache(cache_key, data, source="discogs")
        candidate = _select_discogs_release(data)
        if not candidate:
            return None
        if not _validate_candidate(
            track, candidate.get("title"), candidate.get("artist"), policy=self.validation_policy
        ):
            return None
        track.title = track.title or candidate.get("title")
        track.artist = track.artist or candidate.get("artist")
        track.genre = track.genre or candidate.get("genre")
        track.album = track.album or candidate.get("album")
        track.publisher = track.publisher or candidate.get("label")
        track.year = track.year or candidate.get("year")
        track.copyright = track.copyright or candidate.get("label")
        return track

    def _fetch_musicbrainz_recording(self, recording_id: str) -> dict[str, Any] | None:
        cache_key = f"musicbrainz:recording:{recording_id}"
        cached = get_metadata_cache(cache_key, self.cache_ttl_seconds)
        if cached:
            return cached
        url = f"https://musicbrainz.org/ws/2/recording/{recording_id}"
        params = {"fmt": "json", "inc": "artists+releases+tags+isrcs+media"}
        headers = {"User-Agent": f"{self.musicbrainz_app}/0.1 (local)"}
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            set_metadata_cache(cache_key, data, source="musicbrainz")
            return data
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
        if album and _is_compilation_album(album):
            album = None
    labels = result.get("label", [])
    label = labels[0] if labels else None
    return {
        "title": album or title,
        "artist": artist,
        "genre": (result.get("genre") or [None])[0],
        "album": album,
        "label": label,
        "year": result.get("year"),
    }


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
        acoustid_key: str | None,
        musicbrainz_app: str | None,
        discogs_token: str | None,
        validation_policy: str | None = None,
        cache_ttl_days: int = 30,
    ):
        self.acoustid_key = acoustid_key
        self.musicbrainz_app = musicbrainz_app
        self.discogs_token = discogs_token
        self.validation_policy = validation_policy or "balanced"
        self.cache_ttl_days = cache_ttl_days

    def fill_missing(self, track: Track, method: str) -> Track | None:
        report = self.fill_missing_with_report(track, method)
        return track if report.changed_fields else None

    def fill_missing_with_report(self, track: Track, method: str) -> MetadataFillReport:
        enricher = MetadataEnricher(
            self.acoustid_key,
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
            "acoustid": "online", "musicbrainz": "online", "discogs": "online",
            "text_search": "online", "online_hybrid": "mix",
        }
        resolved = legacy_map.get(method, method)

        if resolved == "offline":
            self._run_local_sources(track, report)
            self._run_local_library_source(track, report)
        elif resolved == "online":
            self._run_online_pipeline(enricher, track, report, include_acoustid=True)
        elif resolved == "mix":
            self._run_local_sources(track, report)
            self._run_local_library_source(track, report)
            self._run_online_pipeline(enricher, track, report, include_acoustid=True)
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
            "albumartist": "albumartist", "year": "year", "genre": "genre",
            "tracknumber": "tracknumber", "discnumber": "discnumber",
            "composer": "composer", "key": "key", "bpm": "bpm",
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
            "tracknumber", "discnumber", "composer", "comment", "isrc", "publisher", "grouping", "copyright", "remixer",
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
            "composer", "publisher", "grouping", "copyright",
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
        for candidate in list_tracks():
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
            "tracknumber", "discnumber", "composer", "comment", "isrc", "publisher", "grouping", "copyright", "remixer",
        })
        report.sources.append(SourceProbe("local_library", LOCAL_SOURCE_LABELS["local_library"], "hit" if fields else "miss", fields=fields, detail=Path(match.path).name))

    def _run_online_pipeline(
        self,
        enricher: MetadataEnricher,
        track: Track,
        report: MetadataFillReport,
        *,
        include_acoustid: bool,
        only: str | None = None,
    ) -> None:
        if include_acoustid and (only in {None, "acoustid"}):
            self._run_acoustid_source(enricher, track, report)
            if only == "acoustid":
                return
        if only in {None, "musicbrainz"}:
            self._run_musicbrainz_source(enricher, track, report)
            if only == "musicbrainz":
                return
        if only in {None, "discogs"}:
            self._run_discogs_source(enricher, track, report)

    def _run_acoustid_source(self, enricher: MetadataEnricher, track: Track, report: MetadataFillReport) -> None:
        before = deepcopy(track)
        enriched = enricher.enrich_track(track)
        fields = _collect_changed_fields(before, track)
        report.sources.append(SourceProbe("acoustid", LOCAL_SOURCE_LABELS["acoustid"], "hit" if enriched and fields else "miss", fields=fields))
        if track.artwork_path and before.artwork_path != track.artwork_path:
            report.sources.append(SourceProbe("cover_art_archive", LOCAL_SOURCE_LABELS["cover_art_archive"], "hit", fields=["artwork_path"], detail=track.artwork_path))

    def _run_musicbrainz_source(self, enricher: MetadataEnricher, track: Track, report: MetadataFillReport) -> None:
        before = deepcopy(track)
        enriched = enricher.enrich_from_musicbrainz_search(track)
        fields = _collect_changed_fields(before, track)
        report.sources.append(SourceProbe("musicbrainz_search", LOCAL_SOURCE_LABELS["musicbrainz_search"], "hit" if enriched and fields else "miss", fields=fields))

    def _run_discogs_source(self, enricher: MetadataEnricher, track: Track, report: MetadataFillReport) -> None:
        before = deepcopy(track)
        enriched = enricher.enrich_from_discogs_search(track, self.discogs_token)
        fields = _collect_changed_fields(before, track)
        report.sources.append(SourceProbe("discogs_search", LOCAL_SOURCE_LABELS["discogs_search"], "hit" if enriched and fields else "miss", fields=fields))


def available_metadata_methods() -> dict[str, str]:
    return dict(METHOD_CATALOG)


def _copy_missing_fields(target: Track, source: Track, allowed: set[str]) -> list[str]:
    changed: list[str] = []
    for field_name in allowed:
        source_value = getattr(source, field_name, None)
        target_value = getattr(target, field_name, None)
        if _has_value(source_value) and not _has_value(target_value):
            setattr(target, field_name, source_value)
            changed.append(field_name)
    return sorted(changed)


def _apply_mapping(target: Track, payload: dict[str, Any], field_map: dict[str, str]) -> list[str]:
    changed: list[str] = []
    for source_key, field_name in field_map.items():
        value = payload.get(source_key)
        if not _has_value(value):
            continue
        if _has_value(getattr(target, field_name, None)):
            continue
        setattr(target, field_name, value)
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
    "bpm", "key", "mood", "energy",
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
