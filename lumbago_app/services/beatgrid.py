from __future__ import annotations

from typing import Iterable


def compute_beatgrid(duration_s: int | None, bpm: float | None) -> list[float]:
    if not duration_s or not bpm or bpm <= 0:
        return []
    interval = 60.0 / bpm
    if interval <= 0:
        return []
    beats: list[float] = []
    current = 0.0
    end = float(duration_s)
    while current <= end:
        beats.append(round(current, 3))
        current += interval
    return beats


def auto_cue_points(duration_s: int | None) -> tuple[int | None, int | None]:
    if not duration_s or duration_s <= 0:
        return None, None
    cue_in = 0
    outro_start = max(duration_s - 10, 0)
    cue_out = int(outro_start * 1000)
    return cue_in, cue_out
