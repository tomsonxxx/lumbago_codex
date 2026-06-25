"""Wybór konkretnego stylu/subgatunku zamiast ogólnych etykiet (Electronic, Dance)."""

from __future__ import annotations

import re
from typing import Any

# Ogólne kategorie — odrzucamy lub traktujemy jako słabe.
BROAD_GENRES: frozenset[str] = frozenset(
    {
        "electronic",
        "electronica",
        "dance",
        "edm",
        "rock",
        "pop",
        "hip hop",
        "hip-hop",
        "rap",
        "jazz",
        "classical",
        "blues",
        "folk",
        "metal",
        "indie",
        "alternative",
        "r&b",
        "rnb",
        "soul",
        "funk",
        "world",
        "misc",
        "miscellaneous",
        "other",
        "unknown",
        "various",
        "soundtrack",
        "audiobook",
        "podcast",
    }
)

# Pojedyncze słowa — lepsze niż Electronic, ale nadal mało szczegółowe.
GENERIC_SUBGENRES: frozenset[str] = frozenset(
    {
        "house",
        "techno",
        "trance",
        "ambient",
        "dubstep",
        "garage",
        "dnb",
        "drum and bass",
        "drum & bass",
        "breakbeat",
        "hardstyle",
        "psytrance",
        "disco",
    }
)

_COMPOUND_HINTS = (
    "house",
    "techno",
    "trance",
    "garage",
    "bass",
    "core",
    "wave",
    "step",
    "hop",
    "jungle",
    "ambient",
    "dub",
)


def normalize_genre_text(value: Any) -> str:
    if value is None:
        return ""
    text = " ".join(str(value).strip().split())
    return text


def is_broad_genre(value: Any) -> bool:
    text = normalize_genre_text(value).lower()
    if not text:
        return True
    if text in BROAD_GENRES:
        return True
    # "Electronic Music", "Dance / Electronic"
    tokens = re.split(r"[/,&]| and ", text)
    stripped = [part.strip() for part in tokens if part.strip()]
    if stripped and all(part in BROAD_GENRES for part in stripped):
        return True
    return False


def genre_specificity_score(value: Any) -> int:
    """Wyższy wynik = bardziej szczegółowy styl."""
    text = normalize_genre_text(value)
    if not text:
        return 0
    lowered = text.lower()
    if is_broad_genre(lowered):
        return 0

    score = len(text)
    words = [part for part in re.split(r"[\s/&,+-]+", lowered) if part]
    if len(words) >= 2:
        score += 12
    if any(hint in lowered for hint in _COMPOUND_HINTS) and len(words) >= 2:
        score += 10
    if lowered in GENERIC_SUBGENRES:
        score = max(score, 8)
    if re.search(r"\b\d{2}s\b", lowered):
        score += 4
    return score


def should_upgrade_genre(current: Any, proposed: Any) -> bool:
    current_text = normalize_genre_text(current)
    proposed_text = normalize_genre_text(proposed)
    if not proposed_text:
        return False
    if not current_text:
        return True
    if is_broad_genre(current_text) and not is_broad_genre(proposed_text):
        return True
    current_score = genre_specificity_score(current_text)
    proposed_score = genre_specificity_score(proposed_text)
    if proposed_score >= current_score + 6:
        return True
    if current_score <= 8 and proposed_score >= 14:
        return True
    return False


def pick_most_specific_genre(
    values: list[str],
    *,
    current: str | None = None,
    min_score: int = 6,
) -> str | None:
    """Wybierz najbardziej szczegółowy gatunek z listy propozycji."""
    ranked: list[tuple[int, str]] = []
    seen: set[str] = set()
    for raw in values:
        text = normalize_genre_text(raw)
        if not text:
            continue
        key = text.casefold()
        if key in seen:
            continue
        seen.add(key)
        spec = genre_specificity_score(text)
        if spec < min_score and is_broad_genre(text):
            continue
        ranked.append((spec, text))

    if not ranked:
        return normalize_genre_text(current) or None

    ranked.sort(key=lambda item: item[0], reverse=True)
    best = ranked[0][1]
    if current and not should_upgrade_genre(current, best):
        return normalize_genre_text(current) or best
    return best


def collect_genre_values_from_candidates(candidates: list[Any]) -> list[str]:
    """Zbierz genre + tagi ze źródeł autotagu."""
    values: list[str] = []
    for candidate in candidates:
        genre = normalize_genre_text(getattr(candidate, "genre", None))
        if genre:
            values.append(genre)
        for tag in getattr(candidate, "tags", []) or []:
            tag_text = normalize_genre_text(tag)
            if tag_text:
                values.append(tag_text)
        remixer = normalize_genre_text(getattr(candidate, "remixer", None))
        if remixer and not is_broad_genre(remixer):
            values.append(remixer)
    return values


def genre_effective_weight(base_score: float, value: Any) -> float:
    """Modyfikator wagi konsensusu — promuje szczegółowe style."""
    text = normalize_genre_text(value)
    if not text:
        return base_score
    spec = genre_specificity_score(text)
    weight = base_score * (1.0 + (spec / 35.0))
    if is_broad_genre(text):
        weight *= 0.70  # lowered penalty so good portal evidence (theaudiodb etc) for broad genres like "Metal" still passes threshold when no more specific data
    elif spec <= 8:
        weight *= 0.75
    return weight