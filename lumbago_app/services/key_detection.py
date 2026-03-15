from __future__ import annotations

from pathlib import Path


MAJOR_PROFILE = [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88]
MINOR_PROFILE = [6.33, 2.68, 3.52, 5.38, 2.6, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17]
KEY_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def detect_key(path: Path, duration_s: int = 60) -> str | None:
    try:
        import numpy as np
        import librosa
    except Exception:
        return None
    try:
        y, sr = librosa.load(path, sr=22050, mono=True, duration=duration_s)
    except Exception:
        return None
    if y is None or len(y) == 0:
        return None
    try:
        chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
        profile = chroma.mean(axis=1)
    except Exception:
        return None
    return _estimate_key(profile)


def _estimate_key(profile) -> str | None:
    try:
        import numpy as np
    except Exception:
        return None
    prof = _normalize(profile)
    major = _normalize(np.array(MAJOR_PROFILE, dtype=float))
    minor = _normalize(np.array(MINOR_PROFILE, dtype=float))
    if prof is None or major is None or minor is None:
        return None
    best_key = None
    best_score = -1e9
    for idx in range(12):
        score_major = float(np.dot(prof, np.roll(major, idx)))
        if score_major > best_score:
            best_score = score_major
            best_key = f"{KEY_NAMES[idx]} major"
        score_minor = float(np.dot(prof, np.roll(minor, idx)))
        if score_minor > best_score:
            best_score = score_minor
            best_key = f"{KEY_NAMES[idx]} minor"
    if not best_key:
        return None
    return _to_camelot(best_key) or _format_key(best_key)


def _normalize(values):
    try:
        import numpy as np
    except Exception:
        return None
    vec = np.array(values, dtype=float)
    total = np.sum(vec)
    if total <= 0:
        return None
    return vec / total


def _format_key(name: str) -> str:
    if name.endswith("minor"):
        return name.replace(" minor", "m")
    if name.endswith("major"):
        return name.replace(" major", "")
    return name


def _to_camelot(name: str) -> str | None:
    mapping = {
        "C major": "8B",
        "G major": "9B",
        "D major": "10B",
        "A major": "11B",
        "E major": "12B",
        "B major": "1B",
        "F# major": "2B",
        "C# major": "3B",
        "G# major": "4B",
        "D# major": "5B",
        "A# major": "6B",
        "F major": "7B",
        "A minor": "8A",
        "E minor": "9A",
        "B minor": "10A",
        "F# minor": "11A",
        "C# minor": "12A",
        "G# minor": "1A",
        "D# minor": "2A",
        "A# minor": "3A",
        "F minor": "4A",
        "C minor": "5A",
        "G minor": "6A",
        "D minor": "7A",
    }
    return mapping.get(name)
