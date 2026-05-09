from __future__ import annotations

from collections import Counter
from dataclasses import replace

from lumbago_app.core.models import AnalysisResult, Track


_UNKNOWN_VALUES = {"", "unknown", "n/a", "none", "null", "-", "\u2014", "â€”"}


def _is_unknown(value: str | None) -> bool:
    if value is None:
        return True
    return value.strip().lower() in _UNKNOWN_VALUES


# AI always overwrites these (audio analysis fields)
_AI_ANALYSIS_TEXT_FIELDS = ("key", "genre", "mood")
_AI_ANALYSIS_FLOAT_FIELDS = ("bpm", "energy")

# Always overwrite with AI-verified values
_META_OVERWRITE_FIELDS = (
    "title", "artist",
    "album", "albumartist", "year",
    "tracknumber", "discnumber", "composer",
    "isrc", "publisher", "lyrics", "grouping", "copyright", "remixer", "comment",
)


def _merge_analysis_into_track(track: Track, result: AnalysisResult) -> Track:
    """Merge AI analysis into a track, overwriting all fields with verified values."""
    for field in _AI_ANALYSIS_TEXT_FIELDS:
        incoming = getattr(result, field, None)
        if incoming is None:
            continue
        if isinstance(incoming, str) and _is_unknown(incoming):
            continue
        if field == "genre" and isinstance(incoming, str):
            incoming = _normalize_genre(incoming)
        setattr(track, field, incoming)

    for field in _AI_ANALYSIS_FLOAT_FIELDS:
        incoming = getattr(result, field, None)
        if incoming is not None:
            setattr(track, field, incoming)

    rating = getattr(result, "rating", None)
    if rating is not None:
        try:
            rating_int = int(rating)
        except (TypeError, ValueError):
            rating_int = None
        if rating_int is not None:
            if rating_int > 5:
                rating_int = max(0, min(5, round(rating_int / 2)))
            if 0 <= rating_int <= 5:
                track.rating = rating_int

    for field in _META_OVERWRITE_FIELDS:
        incoming = getattr(result, field, None)
        if incoming is None:
            continue
        if isinstance(incoming, str) and _is_unknown(incoming):
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
