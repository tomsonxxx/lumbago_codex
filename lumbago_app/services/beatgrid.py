from __future__ import annotations

from typing import Iterable


def detect_bpm(path: str, max_duration: float = 60.0) -> float | None:
    """Wykrywa BPM z pliku audio używając librosa. Zwraca None przy błędzie."""
    try:
        import librosa  # opcjonalna zależność
        y, sr = librosa.load(path, mono=True, duration=max_duration, sr=22050)
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        bpm = float(tempo[0]) if hasattr(tempo, "__len__") else float(tempo)
        if 40.0 <= bpm <= 220.0:
            return round(bpm, 1)
        return None
    except Exception:
        return None


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
