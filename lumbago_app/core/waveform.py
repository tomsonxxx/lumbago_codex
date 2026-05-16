from __future__ import annotations

import math
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

from PyQt6 import QtGui

from lumbago_app.core.config import cache_dir


@dataclass
class WaveformData:
    """Przechowuje surowe piki waveformy jako listę wartości float [0.0, 1.0]."""

    peaks: list[float] = field(default_factory=list)
    duration_s: float = 0.0

    def is_empty(self) -> bool:
        """Zwraca True jeśli brak danych waveformy."""
        return len(self.peaks) == 0

    def normalized_peaks(self, target_width: int = 600) -> list[float]:
        """Zwraca listę pików przeskalowanych do target_width próbek, wartości w [0.0, 1.0]."""
        if self.is_empty():
            return [0.0] * target_width
        src = self.peaks
        n = len(src)
        if n == target_width:
            return list(src)
        result: list[float] = []
        for i in range(target_width):
            src_i = i * n / target_width
            lo = int(src_i)
            hi = min(lo + 1, n - 1)
            frac = src_i - lo
            result.append(src[lo] * (1 - frac) + src[hi] * frac)
        return result


def waveform_cache_path(audio_path: Path) -> Path:
    safe_name = audio_path.stem.replace(" ", "_")
    return cache_dir() / f"{safe_name}_waveform.png"


def generate_waveform_threadsafe(audio_path: Path, width: int = 600, height: int = 120) -> Path | None:
    """Thread-safe waveform generation using ffmpeg only — no Qt."""
    path = waveform_cache_path(audio_path)
    if path.exists():
        return path
    if _try_ffmpeg_waveform(audio_path, path, width, height):
        return path
    return None


def generate_waveform(audio_path: Path, width: int = 600, height: int = 120) -> Path:
    path = waveform_cache_path(audio_path)
    if path.exists():
        return path
    if _try_ffmpeg_waveform(audio_path, path, width, height):
        return path
    return generate_waveform_placeholder(audio_path, width=120, height=24)


def generate_waveform_placeholder(audio_path: Path, width: int = 120, height: int = 24) -> Path:
    path = waveform_cache_path(audio_path)
    if path.exists():
        return path
    pixmap = QtGui.QPixmap(width, height)
    pixmap.fill(QtGui.QColor("#0e1220"))
    painter = QtGui.QPainter(pixmap)
    painter.setPen(QtGui.QColor("#39ff14"))
    mid = height // 2
    for x in range(0, width, 4):
        h = int((math.sin((x / width) * math.pi * 4) + 1) * (height / 4)) + 2
        painter.drawLine(x, mid - h, x, mid + h)
    painter.end()
    pixmap.save(str(path))
    return path


def _try_ffmpeg_waveform(audio_path: Path, output_path: Path, width: int, height: int) -> bool:
    try:
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            str(audio_path),
            "-filter_complex",
            f"showwavespic=s={width}x{height}:colors=0x39ff14",
            str(output_path),
        ]
        subprocess.run(cmd, capture_output=True, check=True)
        return output_path.exists()
    except Exception:
        return False
