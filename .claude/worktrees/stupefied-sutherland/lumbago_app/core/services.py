from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from lumbago_app.core.audio import file_hash
from lumbago_app.services.recognizer import AcoustIdRecognizer
from lumbago_app.core.models import AnalysisResult, DuplicateGroup, Track


def heuristic_analysis(track: Track) -> AnalysisResult:
    bpm = track.bpm
    energy = None
    mood = None
    if bpm:
        if bpm < 90:
            energy, mood = 0.2, "chill"
        elif bpm < 120:
            energy, mood = 0.5, "groove"
        elif bpm < 140:
            energy, mood = 0.75, "energetic"
        else:
            energy, mood = 0.9, "peak"
    return AnalysisResult(
        bpm=bpm,
        key=track.key,
        mood=mood,
        energy=energy,
        genre=track.genre,
        description=None,
        confidence=0.4,
    )


@dataclass
class DuplicateResult:
    groups: list[DuplicateGroup]


def find_duplicates_by_hash(paths: Iterable[Path]) -> DuplicateResult:
    hashes: dict[str, list[int]] = {}
    index: dict[int, Path] = {}
    for idx, path in enumerate(paths, 1):
        index[idx] = path
        h = file_hash(path)
        hashes.setdefault(h, []).append(idx)
    groups = [DuplicateGroup(track_ids=ids, similarity=1.0) for ids in hashes.values() if len(ids) > 1]
    return DuplicateResult(groups=groups)


def find_duplicates_by_tags(tracks: Iterable[Track]) -> DuplicateResult:
    buckets: dict[tuple[str, str, int], list[int]] = {}
    for idx, track in enumerate(tracks, 1):
        title = (track.title or "").strip().lower()
        artist = (track.artist or "").strip().lower()
        duration = int(track.duration or 0)
        key = (title, artist, duration)
        buckets.setdefault(key, []).append(idx)
    groups = [DuplicateGroup(track_ids=ids, similarity=0.9) for ids in buckets.values() if len(ids) > 1]
    return DuplicateResult(groups=groups)


def find_duplicates_by_fingerprint(paths: Iterable[Path]) -> DuplicateResult:
    recognizer = AcoustIdRecognizer(api_key=None)
    fingerprints: dict[str, list[int]] = {}
    index: dict[int, Path] = {}
    for idx, path in enumerate(paths, 1):
        index[idx] = path
        try:
            fp = recognizer.fingerprint(path)
        except Exception:
            fp = None
        if not fp:
            continue
        _, fingerprint = fp
        fingerprints.setdefault(fingerprint, []).append(idx)
    groups = [DuplicateGroup(track_ids=ids, similarity=0.95) for ids in fingerprints.values() if len(ids) > 1]
    return DuplicateResult(groups=groups)
