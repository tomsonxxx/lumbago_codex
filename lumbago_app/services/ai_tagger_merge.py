from __future__ import annotations

from collections import Counter
from dataclasses import replace

from lumbago_app.core.models import AnalysisResult, Track


_UNKNOWN_VALUES = {"", "unknown", "n/a", "none", "null", "-", "\u2014", "â€”"}
_JUNK_SUBSTRINGS = ("www.", "http://", "https://", "track ", "untitled", "audio track")


def _is_unknown(value: str | None) -> bool:
    if value is None:
        return True
    return value.strip().lower() in _UNKNOWN_VALUES


def _is_junk(value: str | None) -> bool:
    if value is None:
        return True
    text = value.strip().lower()
    if text in _UNKNOWN_VALUES:
        return True
    return any(token in text for token in _JUNK_SUBSTRINGS)


def _prefer_incoming(local_value: str | None, incoming_value: str | None) -> bool:
    if incoming_value is None or _is_unknown(incoming_value):
        return False
    if local_value is None or _is_unknown(local_value) or _is_junk(local_value):
        return True
    local_len = len(local_value.strip())
    incoming_len = len(incoming_value.strip())
    return incoming_len >= max(local_len + 4, int(local_len * 1.3))


_AI_ANALYSIS_TEXT_FIELDS = ("key", "genre", "mood")
_AI_ANALYSIS_FLOAT_FIELDS = ("bpm", "energy")
_META_OVERWRITE_FIELDS = (
    "title", "artist",
    "album", "albumartist", "year",
    "tracknumber", "discnumber", "composer",
    "isrc", "publisher", "lyrics", "grouping", "copyright", "remixer", "comment",
)


def _merge_analysis_into_track(track: Track, result: AnalysisResult) -> Track:
    """Non-destructive merge: keep good local values, fill blanks, replace junk."""
    for field in _AI_ANALYSIS_TEXT_FIELDS:
        incoming = getattr(result, field, None)
        if incoming is None or (isinstance(incoming, str) and _is_unknown(incoming)):
            continue
        local_value = getattr(track, field, None)
        if isinstance(local_value, str) and not _prefer_incoming(local_value, incoming):
            continue
        if field == "genre" and isinstance(incoming, str):
            incoming = _normalize_genre(incoming)
        setattr(track, field, incoming)

    for field in _AI_ANALYSIS_FLOAT_FIELDS:
        incoming = getattr(result, field, None)
        local_value = getattr(track, field, None)
        if incoming is not None and local_value is None:
            setattr(track, field, incoming)

    rating = getattr(result, "rating", None)
    if rating is not None:
        try:
            rating_int = int(rating)
        except (TypeError, ValueError):
            rating_int = None
        if rating_int is not None and 0 <= rating_int <= 5:
            if track.rating in (None, 0):
                track.rating = rating_int

    for field in _META_OVERWRITE_FIELDS:
        incoming = getattr(result, field, None)
        if incoming is None or (isinstance(incoming, str) and _is_unknown(incoming)):
            continue
        local_value = getattr(track, field, None)
        if isinstance(incoming, str):
            local_text = str(local_value) if local_value is not None else None
            if not _prefer_incoming(local_text, incoming):
                continue
        elif local_value not in (None, ""):
            continue
        setattr(track, field, incoming)

    return track


def _normalize_genre(value: str) -> str:
    cleaned = " ".join(value.strip().split())
    if not cleaned:
        return value
    return cleaned.title()


def _harmonize_batch_results(
    pairs: list[tuple[Track, AnalysisResult]],
) -> list[tuple[Track, AnalysisResult]]:
    """Harmonize batch AI text fields by enforcing majority values for genre and mood."""
    text_fields = ("genre", "mood")

    majorities: dict[str, str] = {}
    for field in text_fields:
        values = [getattr(result, field) for _, result in pairs]
        clean = [v.strip() for v in values if isinstance(v, str) and not _is_unknown(v)]
        if clean:
            majorities[field] = Counter(clean).most_common(1)[0][0]

    harmonized: list[tuple[Track, AnalysisResult]] = []
    for track, result in pairs:
        patched = result
        for field, majority in majorities.items():
            candidate = getattr(patched, field)
            if isinstance(candidate, str) and candidate.strip() and candidate.strip() != majority:
                patched = replace(patched, **{field: majority})
        harmonized.append((track, patched))

    return harmonized
