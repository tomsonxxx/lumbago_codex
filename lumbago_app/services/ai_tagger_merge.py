from __future__ import annotations

from collections import Counter
from dataclasses import replace

from lumbago_app.core.models import AnalysisResult, Track


_UNKNOWN_VALUES = {"", "unknown", "n/a", "none", "null", "-", "\u2014", "â€”"}


def _is_unknown(value: str | None) -> bool:
    if value is None:
        return True
    return value.strip().lower() in _UNKNOWN_VALUES


def _merge_analysis_into_track(track: Track, result: AnalysisResult) -> Track:
    """Merge AI analysis into a track while ignoring textual placeholders like 'Unknown'."""
    for field in ("key", "genre", "mood"):
        incoming = getattr(result, field)
        if incoming is None:
            continue
        if isinstance(incoming, str) and _is_unknown(incoming):
            continue
        setattr(track, field, incoming)

    for field in ("bpm", "energy"):
        incoming = getattr(result, field)
        if incoming is not None:
            setattr(track, field, incoming)

    return track


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
