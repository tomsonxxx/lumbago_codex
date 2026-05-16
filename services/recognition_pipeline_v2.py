from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path, PureWindowsPath
import logging
import re
from typing import Any

from core.models import Track
from core.renamer import parse_filename_tags
from services.free_music_portals import FreeMusicPortalSearch, PortalCandidate, PortalProbe
from services.metadata_consensus import FieldEvidence
from services.metadata_providers import (
    MusicBrainzProvider,
    _best_mbid_from_acoustid,
    _parse_mb_recording,
)
from services.recognizer import AcoustIdRecognizer


log = logging.getLogger(__name__)

RECOGNITION_FIELDS = (
    "title",
    "artist",
    "album",
    "albumartist",
    "year",
    "genre",
    "tracknumber",
    "discnumber",
    "composer",
    "bpm",
    "key",
    "rating",
    "mood",
    "energy",
    "comment",
    "lyrics",
    "isrc",
    "publisher",
    "grouping",
    "copyright",
    "remixer",
)

SOURCE_CONFIDENCE = {
    "acoustid": 0.98,
    "musicbrainz": 0.90,
    "listenbrainz": 0.89,   # dane MusicBrainz przez prostszy endpoint
    "musicbrainz_portal": 0.88,
    "discogs_portal": 0.86,
    "deezer": 0.82,
    "itunes": 0.80,
    "theaudiodb": 0.76,     # dobre dane gatunkowo/nastrój/BPM
    "lastfm": 0.74,
    "soundcloud": 0.74,
    "bandcamp": 0.74,
    "musixmatch": 0.72,
    "youtube": 0.72,
    "audius": 0.72,
    "existing_tags": 0.72,
    "jiosaavn": 0.71,
    "archiveorg": 0.70,
    "genius": 0.68,
    "filename": 0.52,
    "folder_structure": 0.45,
}


@dataclass(frozen=True)
class RecognitionAttempt:
    source: str
    status: str
    detail: str
    confidence: float = 0.0
    fields: tuple[str, ...] = ()


@dataclass(frozen=True)
class RecognitionPipelineResult:
    track: Track
    evidence_by_field: dict[str, list[FieldEvidence]]
    attempts: list[RecognitionAttempt]
    summary: str
    primary_source: str | None = None
    filename_query: str | None = None


class RecognitionPipelineV2:
    def __init__(
        self,
        *,
        acoustid_api_key: str | None = None,
        recognizer: AcoustIdRecognizer | None = None,
        portal_search: FreeMusicPortalSearch | None = None,
        musicbrainz_provider: MusicBrainzProvider | None = None,
        portal_query_limit: int = 3,
        musicbrainz_app_name: str | None = None,
        discogs_token: str | None = None,
        lastfm_api_key: str | None = None,
        musixmatch_api_key: str | None = None,
        genius_api_key: str | None = None,
    ) -> None:
        self.recognizer = recognizer or AcoustIdRecognizer(acoustid_api_key)
        self.portal_search = portal_search or FreeMusicPortalSearch(
            musicbrainz_app_name=musicbrainz_app_name,
            discogs_token=discogs_token,
            lastfm_api_key=lastfm_api_key,
            musixmatch_api_key=musixmatch_api_key,
            genius_api_key=genius_api_key,
        )
        self.musicbrainz_provider = musicbrainz_provider or MusicBrainzProvider(
            app_name=musicbrainz_app_name
        )
        self.portal_query_limit = max(1, portal_query_limit)

    def recognize_track(
        self,
        track: Track,
        *,
        refresh_existing: bool = False,
        query_track: Track | None = None,
    ) -> RecognitionPipelineResult:
        working = deepcopy(track)
        if refresh_existing:
            _reset_track_for_refresh(working)
        search_source = deepcopy(query_track or track)
        observed_at = datetime.utcnow()
        evidence_by_field: dict[str, list[FieldEvidence]] = {}
        attempts: list[RecognitionAttempt] = []

        self._add_filename_evidence(working, search_source, evidence_by_field, observed_at, attempts)

        fingerprint_hit = self._recognize_from_fingerprint(working, evidence_by_field, observed_at, attempts)
        portal_hit = False
        if not fingerprint_hit:
            portal_hit = self._recognize_from_portals(
                working,
                search_source,
                evidence_by_field,
                observed_at,
                attempts,
            )

        primary_source: str | None = None
        if fingerprint_hit:
            primary_source = "acoustid"
        elif portal_hit:
            primary_source = self._best_portal_source(attempts)
        elif any(attempt.status == "hit" for attempt in attempts):
            primary_source = next((attempt.source for attempt in attempts if attempt.status == "hit"), None)

        summary = self._build_summary(attempts)
        return RecognitionPipelineResult(
            track=working,
            evidence_by_field=evidence_by_field,
            attempts=attempts,
            summary=summary,
            primary_source=primary_source,
            filename_query=_build_filename_query(search_source),
        )

    def _add_filename_evidence(
        self,
        track: Track,
        query_source: Track,
        evidence_by_field: dict[str, list[FieldEvidence]],
        observed_at: datetime,
        attempts: list[RecognitionAttempt],
    ) -> None:
        artist_from_file, title_from_file = parse_filename_tags(track.path)
        stem = _clean_filename_text(PureWindowsPath(query_source.path).stem)
        repaired = False

        if title_from_file and (
            not _has_value(track.title)
            or _looks_like_track_number(track.title)
            or _looks_like_quality_title(track.title)
        ):
            track.title = title_from_file
            repaired = True
        if artist_from_file and not _has_value(track.artist):
            track.artist = artist_from_file
            repaired = True

        filename_fields: dict[str, str] = {}
        if _has_value(track.title):
            filename_fields["title"] = str(track.title)
        elif title_from_file:
            filename_fields["title"] = title_from_file
        if _has_value(track.artist):
            filename_fields["artist"] = str(track.artist)
        elif artist_from_file:
            filename_fields["artist"] = artist_from_file
        if stem and not filename_fields.get("title"):
            guessed_title = _guess_title_from_stem(stem, artist_from_file)
            if guessed_title:
                filename_fields["title"] = guessed_title

        if repaired or filename_fields:
            attempts.append(
                RecognitionAttempt(
                    source="filename",
                    status="hit" if filename_fields else "miss",
                    detail="Filename normalization",
                    confidence=SOURCE_CONFIDENCE["filename"],
                    fields=tuple(sorted(filename_fields)),
                )
            )

        for field_name, value in filename_fields.items():
            _append_evidence(
                evidence_by_field,
                field_name,
                value,
                source="filename",
                confidence=SOURCE_CONFIDENCE["filename"],
                verified=False,
                timestamp=observed_at,
            )

        if _has_value(track.albumartist):
            _append_evidence(
                evidence_by_field,
                "albumartist",
                track.albumartist,
                source="existing_tags",
                confidence=SOURCE_CONFIDENCE["existing_tags"],
                verified=False,
                timestamp=observed_at,
            )

    def _recognize_from_fingerprint(
        self,
        track: Track,
        evidence_by_field: dict[str, list[FieldEvidence]],
        observed_at: datetime,
        attempts: list[RecognitionAttempt],
    ) -> bool:
        audio_path = Path(track.path)
        if not audio_path.exists():
            attempts.append(
                RecognitionAttempt(
                    source="acoustid",
                    status="miss",
                    detail="Audio file not found",
                    confidence=SOURCE_CONFIDENCE["acoustid"],
                )
            )
            return False

        fingerprint_fn = getattr(self.recognizer, "fingerprint", None)
        if callable(fingerprint_fn):
            try:
                fingerprint = fingerprint_fn(audio_path)
            except Exception as exc:
                log.warning("Fingerprint generation failed for %s: %s", audio_path, exc)
                attempts.append(
                    RecognitionAttempt(
                        source="acoustid",
                        status="error",
                        detail=f"fingerprint: {exc}",
                        confidence=SOURCE_CONFIDENCE["acoustid"],
                    )
                )
            else:
                if fingerprint and not _has_value(track.fingerprint):
                    track.fingerprint = fingerprint[1]
                if not getattr(self.recognizer, "api_key", None):
                    attempts.append(
                        RecognitionAttempt(
                            source="acoustid",
                            status="miss",
                            detail="Fingerprint generated locally, lookup skipped because no API key is configured",
                            confidence=SOURCE_CONFIDENCE["acoustid"],
                            fields=("fingerprint",) if fingerprint else (),
                        )
                    )
                    return False

        try:
            payload = self.recognizer.recognize(audio_path)
        except Exception as exc:
            log.warning("AcoustID recognition failed for %s: %s", audio_path, exc)
            attempts.append(
                RecognitionAttempt(
                    source="acoustid",
                    status="error",
                    detail=str(exc),
                    confidence=SOURCE_CONFIDENCE["acoustid"],
                )
            )
            return False

        if not payload:
            attempts.append(
                RecognitionAttempt(
                    source="acoustid",
                    status="miss",
                    detail="No fingerprint match",
                    confidence=SOURCE_CONFIDENCE["acoustid"],
                )
            )
            return False

        mbid = _best_mbid_from_acoustid(payload)
        if not mbid:
            attempts.append(
                RecognitionAttempt(
                    source="acoustid",
                    status="miss",
                    detail="Fingerprint matched but no MusicBrainz recording was returned",
                    confidence=SOURCE_CONFIDENCE["acoustid"],
                )
            )
            return False

        recording = self.musicbrainz_provider.get_recording(mbid)
        if not recording:
            attempts.append(
                RecognitionAttempt(
                    source="acoustid",
                    status="hit",
                    detail=f"Matched MBID {mbid}",
                    confidence=SOURCE_CONFIDENCE["acoustid"],
                    fields=(),
                )
            )
            return False

        meta = _parse_mb_recording(recording)
        if not meta:
            attempts.append(
                RecognitionAttempt(
                    source="acoustid",
                    status="hit",
                    detail=f"Matched MBID {mbid} but no flat metadata could be parsed",
                    confidence=SOURCE_CONFIDENCE["acoustid"],
                )
            )
            return False

        for field_name, value in meta.items():
            if not _has_value(value):
                continue
            verified = field_name in {"title", "artist", "album", "albumartist", "year", "isrc"}
            source = "acoustid" if verified else "musicbrainz"
            confidence = SOURCE_CONFIDENCE.get(source, 0.9)
            _append_evidence(
                evidence_by_field,
                field_name,
                value,
                source=source,
                confidence=confidence,
                verified=verified,
                timestamp=observed_at,
            )

        attempts.append(
            RecognitionAttempt(
                source="acoustid",
                status="hit",
                detail=f"Matched MBID {mbid}",
                confidence=SOURCE_CONFIDENCE["acoustid"],
                fields=tuple(sorted(meta)),
            )
        )
        return True

    def _recognize_from_portals(
        self,
        track: Track,
        query_source: Track,
        evidence_by_field: dict[str, list[FieldEvidence]],
        observed_at: datetime,
        attempts: list[RecognitionAttempt],
    ) -> bool:
        queries = _build_portal_queries(track, query_source=query_source)
        if not queries:
            attempts.append(
                RecognitionAttempt(
                    source="portal",
                    status="miss",
                    detail="No usable portal query could be built",
                    confidence=0.0,
                )
            )
            return False

        seen_pairs: set[tuple[str, str]] = set()
        hits: list[tuple[PortalProbe, PortalCandidate, str, float]] = []
        for query in queries[: self.portal_query_limit]:
            try:
                probes = self.portal_search.search_all(query)
            except Exception as exc:
                log.warning("Portal search failed for %s: %s", query, exc)
                attempts.append(
                    RecognitionAttempt(
                        source="portal",
                        status="error",
                        detail=f"{query}: {exc}",
                        confidence=0.0,
                    )
                )
                continue
            for probe in probes:
                candidate = probe.candidate
                if candidate is None:
                    attempts.append(
                        RecognitionAttempt(
                            source=probe.source_key,
                            status="miss",
                            detail=f"{query}: {probe.detail}",
                            confidence=SOURCE_CONFIDENCE.get(probe.source_key, 0.6),
                        )
                    )
                    continue
                pair_key = (probe.source_key, query)
                if pair_key in seen_pairs:
                    continue
                seen_pairs.add(pair_key)
                score = _score_portal_candidate(track, probe.source_key, candidate)
                hits.append((probe, candidate, query, score))
                attempts.append(
                    RecognitionAttempt(
                        source=probe.source_key,
                        status="hit",
                        detail=f"{query}: {probe.detail}",
                        confidence=score,
                        fields=tuple(
                            field_name
                            for field_name in RECOGNITION_FIELDS
                            if _has_value(getattr(candidate, field_name, None))
                        ),
                    )
                )

        if not hits:
            return False

        hits.sort(key=lambda item: item[3], reverse=True)
        for probe, candidate, query, score in hits[:5]:
            self._append_candidate_evidence(
                evidence_by_field,
                candidate,
                source=probe.source_key,
                confidence=score,
                observed_at=observed_at,
            )

        return True

    def _append_candidate_evidence(
        self,
        evidence_by_field: dict[str, list[FieldEvidence]],
        candidate: PortalCandidate,
        *,
        source: str,
        confidence: float,
        observed_at: datetime,
    ) -> None:
        source_confidence = max(0.0, min(1.0, confidence))
        for field_name in RECOGNITION_FIELDS:
            value = getattr(candidate, field_name, None)
            if not _has_value(value):
                continue
            field_confidence = source_confidence
            if field_name in {"title", "artist", "album", "albumartist"}:
                field_confidence = min(1.0, source_confidence + 0.05)
            elif field_name in {"year", "isrc"}:
                field_confidence = min(1.0, source_confidence + 0.03)
            _append_evidence(
                evidence_by_field,
                field_name,
                value,
                source=source,
                confidence=field_confidence,
                verified=source == "musicbrainz_portal",
                timestamp=observed_at,
            )

    def _best_portal_source(self, attempts: list[RecognitionAttempt]) -> str | None:
        portal_attempts = [attempt for attempt in attempts if attempt.status == "hit" and attempt.source != "acoustid"]
        if not portal_attempts:
            return None
        best = max(portal_attempts, key=lambda attempt: attempt.confidence)
        return best.source

    def _build_summary(self, attempts: list[RecognitionAttempt]) -> str:
        hits = [attempt for attempt in attempts if attempt.status == "hit"]
        misses = [attempt for attempt in attempts if attempt.status == "miss"]
        errors = [attempt for attempt in attempts if attempt.status == "error"]
        if not attempts:
            return "Brak prób rozpoznania"
        parts = [f"trafienia: {len(hits)}", f"braki: {len(misses)}"]
        if errors:
            parts.append(f"błędy: {len(errors)}")
        if hits:
            sources = ", ".join(dict.fromkeys(attempt.source for attempt in hits[:5]))
            parts.insert(0, f"źródła: {sources}")
        return " | ".join(parts)


def _build_portal_queries(track: Track, query_source: Track | None = None) -> list[str]:
    source = query_source or track
    artist = _clean_filename_text(track.artist or source.artist)
    title = _clean_filename_text(track.title or source.title)
    album = _clean_filename_text(track.album or source.album)
    albumartist = _clean_filename_text(track.albumartist or source.albumartist)
    remixer = _clean_filename_text(track.remixer or source.remixer)
    stem = _clean_filename_text(PureWindowsPath(source.path).stem)
    filename_artist, filename_title = parse_filename_tags(source.path)
    filename_artist = _clean_filename_text(filename_artist)
    filename_title = _clean_filename_text(filename_title)

    fragments = [
        (artist, title),
        (title, artist),
        (filename_artist, filename_title),
        (filename_title, filename_artist),
        (title, remixer),
        (artist, title, remixer),
        (remixer, title, artist),
        (artist, album),
        (title, album),
        (albumartist, title),
        (title,),
        (artist,),
        (filename_title,),
        (stem,),
    ]

    seen: set[str] = set()
    queries: list[str] = []
    for fragment_group in fragments:
        raw = " ".join(part for part in fragment_group if part)
        cleaned = _compact_query(raw)
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            queries.append(cleaned)
    return queries[:8]


def _score_portal_candidate(track: Track, source: str, candidate: PortalCandidate) -> float:
    title_score = _token_similarity(track.title, candidate.title)
    artist_score = _token_similarity(track.artist or track.albumartist, candidate.artist)
    album_score = _token_similarity(track.album, candidate.album)
    base = (title_score * 0.58) + (artist_score * 0.30) + (album_score * 0.12)
    source_bonus = SOURCE_CONFIDENCE.get(source, 0.65)
    return max(0.0, min(1.0, (base * 0.72) + (source_bonus * 0.28)))


def _append_evidence(
    evidence_by_field: dict[str, list[FieldEvidence]],
    field_name: str,
    value: Any,
    *,
    source: str,
    confidence: float,
    verified: bool,
    timestamp: datetime,
) -> None:
    evidence_by_field.setdefault(field_name, []).append(
        FieldEvidence(
            field_name=field_name,
            value=value,
            source=source,
            confidence=confidence,
            verified=verified,
            timestamp=timestamp,
        )
    )


def _build_filename_query(track: Track) -> str | None:
    queries = _build_portal_queries(track)
    return queries[0] if queries else None


def _compact_query(value: str | None) -> str:
    if not value:
        return ""
    text = _clean_filename_text(value)
    text = re.sub(
        r"\b(official|audio|video|lyrics?|lyric|hq|hd|4k|8k|remaster(?:ed)?|final|master|download|free|explicit|version|edit|mix|radio)\b",
        " ",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(r"\b\d{2,4}\s*(?:kbps|k)?\b", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _clean_filename_text(value: str | None) -> str:
    if not value:
        return ""
    text = str(value)
    text = text.replace("_", " ").replace(".", " ")
    text = re.sub(r"[\[(].*?[\])]", " ", text)
    text = re.sub(r"\b(HQ|HD|4K|8K|FINAL|MASTER|FREE DOWNLOAD|OFFICIAL VIDEO|OFFICIAL AUDIO)\b", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\b(remaster(?:ed)?|live|explicit|version|edit|mix|radio edit)\b", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\b\d{2,4}\s*(?:kbps|k)?\b", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"[^\w\s\-&,()+']", " ", text, flags=re.UNICODE)
    text = re.sub(r"\s+", " ", text).strip(" .-_")
    return text


def _guess_title_from_stem(stem: str, artist_from_file: str | None) -> str | None:
    if not stem:
        return None
    text = _clean_filename_text(stem)
    if artist_from_file:
        pattern = re.escape(_clean_filename_text(artist_from_file))
        text = re.sub(rf"^{pattern}\s*[-–—]\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\b\d{2,4}\s*(?:kbps|k|mp3|flac|wav|m4a|aac)\b", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text).strip(" .-_")
    return text or None


def _token_similarity(left: str | None, right: str | None) -> float:
    if not left or not right:
        return 0.0
    left_tokens = set(_compact_query(left).casefold().split())
    right_tokens = set(_compact_query(right).casefold().split())
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / len(left_tokens | right_tokens)


def _has_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        normalized = value.strip().lower()
        return bool(normalized) and normalized not in {"-", "unknown", "n/a", "none", "null", "brak"}
    return True


def _reset_track_for_refresh(track: Track) -> None:
    for field_name in RECOGNITION_FIELDS:
        if hasattr(track, field_name):
            setattr(track, field_name, None)
    track.rating = 0
    track.tags = []
    track.fingerprint = None
    track.artwork_path = None
    track.waveform_path = None


def _looks_like_track_number(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    return bool(re.fullmatch(r"\d{1,4}", value.strip()))


def _looks_like_quality_title(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    return bool(re.fullmatch(r"\d{2,4}\s*(?:kbps|k)?", value.strip(), re.IGNORECASE))
