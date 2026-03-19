"""Beatgrid Service - obliczenia BPM, siatki beatów i zgodności kluczy Camelot."""
from __future__ import annotations
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_CAMELOT_WHEEL = ["1A","1B","2A","2B","3A","3B","4A","4B","5A","5B","6A","6B",
                  "7A","7B","8A","8B","9A","9B","10A","10B","11A","11B","12A","12B"]


def camelot_adjacent_keys(key: str) -> list[str]:
    key = key.strip().upper()
    if key not in _CAMELOT_WHEEL: return [key]
    results = {key}
    num = int(key[:-1]); letter = key[-1]
    for delta in (-1, 1):
        adj_num = ((num - 1 + delta) % 12) + 1
        adj = f"{adj_num}{letter}"
        if adj in _CAMELOT_WHEEL: results.add(adj)
    other = "B" if letter == "A" else "A"
    same = f"{num}{other}"
    if same in _CAMELOT_WHEEL: results.add(same)
    return sorted(results)


def camelot_range_filter(tracks_with_keys: list[tuple[str,str]], root: str, steps: int = 1) -> list[str]:
    base = root.strip().upper()
    if base not in _CAMELOT_WHEEL: return []
    compatible = {base}
    frontier = {base}
    for _ in range(steps):
        nxt = set()
        for k in frontier:
            for adj in camelot_adjacent_keys(k):
                if adj not in compatible:
                    nxt.add(adj); compatible.add(adj)
        frontier = nxt
    return [ident for ident, k in tracks_with_keys if k.strip().upper() in compatible]


def compute_beatgrid(duration_seconds: float, bpm: float, start_offset: float = 0.0) -> list[float]:
    """Return beat timestamps (seconds) for a simple fixed-tempo beatgrid."""
    if duration_seconds <= 0 or bpm <= 0:
        return []
    interval = 60.0 / bpm
    if interval <= 0:
        return []
    beats: list[float] = []
    current = max(0.0, start_offset)
    while current <= duration_seconds:
        beats.append(round(current, 3))
        current += interval
    return beats


def auto_cue_points(duration_seconds: float, intro_seconds: float = 0.0, outro_padding_seconds: float = 10.0) -> tuple[int, int]:
    """
    Return cue-in and cue-out in milliseconds.
    cue_in starts at intro_seconds, cue_out ends before the track tail.
    """
    duration_seconds = max(0.0, duration_seconds)
    cue_in_ms = int(max(0.0, intro_seconds) * 1000)
    cue_out_seconds = max(0.0, duration_seconds - max(0.0, outro_padding_seconds))
    cue_out_ms = int(cue_out_seconds * 1000)
    if cue_out_ms < cue_in_ms:
        cue_out_ms = cue_in_ms
    return cue_in_ms, cue_out_ms
