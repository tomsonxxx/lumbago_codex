from __future__ import annotations

import math
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

from PyQt6 import QtGui

from core.config import cache_dir


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


# ============================================================
# REUSABLE PEAK EXTRACTION (librosa optional, with robust fallback)
# Used by: DJPlayer WaveformWidget + library detail preview (no ffmpeg dep)
# ============================================================

_HAS_LIBROSA = False
_librosa = None
_np = None

try:
    import librosa as _librosa_mod
    import numpy as _np_mod
    _librosa = _librosa_mod
    _np = _np_mod
    _HAS_LIBROSA = True
except ImportError:
    pass


def extract_peaks(audio_path: str | Path, num_points: int = 600) -> list[float]:
    """
    Wyciąga znormalizowane peaki [0.0-1.0] do rysowania waveformy.
    - Priorytet: librosa (dokładne, szybkie z downsamplingiem)
    - Fallback: proceduralna symulacja (zawsze działa, bez zależności)
    Tłum i ostrzeżenia librosa żeby nie zaśmiecać konsoli.
    """
    path = Path(audio_path)
    if not path.exists():
        return _generate_fallback_peaks(num_points)

    if _HAS_LIBROSA and _librosa is not None and _np is not None:
        try:
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", UserWarning)
                warnings.simplefilter("ignore", FutureWarning)
                y, sr = _librosa.load(str(path), sr=22050, mono=True, duration=None)
            if len(y) == 0:
                return _generate_fallback_peaks(num_points)

            segment_length = max(1, len(y) // num_points)
            peaks: list[float] = []
            for i in range(num_points):
                start = i * segment_length
                end = min((i + 1) * segment_length, len(y))
                segment = y[start:end]
                peak = float(_np.max(_np.abs(segment))) if len(segment) > 0 else 0.0
                peaks.append(min(1.0, peak))

            max_val = max(peaks) if peaks else 1.0
            if max_val > 0:
                peaks = [p / max_val for p in peaks]
            return peaks
        except Exception:
            pass  # fall through to fallback

    return _generate_fallback_peaks(num_points)


def _generate_fallback_peaks(num_points: int) -> list[float]:
    """Proceduralna, przyjemna dla oka symulacja waveformy (bez zewnętrznych zależności)."""
    import math
    import random
    peaks: list[float] = []
    rng = random.Random(42)  # deterministic for same file feel
    for i in range(num_points):
        t = (i / num_points) * 220
        # Bardziej "muzyczny" kształt (kilka harmonicznych + lekkie transjenty)
        base = 0.22 + 0.48 * abs(math.sin(t * 1.85))
        base += 0.18 * abs(math.sin(t * 0.7 + 1.2))
        base += 0.09 * abs(math.sin(t * 3.9))
        noise = rng.uniform(-0.045, 0.045)
        val = max(0.06, min(0.98, base + noise))
        peaks.append(val)
    # Lekka normalizacja
    m = max(peaks) or 1.0
    return [p / m for p in peaks]


def paint_waveform_pixmap(peaks: list[float], width: int, height: int,
                          bg: str = "#0e1220", peak_color: str = "#39ff14",
                          rms_color: str = "#1f6f3a") -> QtGui.QPixmap:
    """
    Rysuje klasyczną waveformę (peak + rms) na QPixmap – zero plików, zero ffmpeg.
    Używane przez panel szczegółów w bibliotece (zamiast generate_waveform z ffmpeg).
    """
    from PyQt6 import QtGui
    pix = QtGui.QPixmap(width, height)
    pix.fill(QtGui.QColor(bg))
    if not peaks:
        return pix

    painter = QtGui.QPainter(pix)
    painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, False)
    n = len(peaks)
    mid = height // 2
    pen_rms = QtGui.QPen(QtGui.QColor(rms_color), 1)
    pen_peak = QtGui.QPen(QtGui.QColor(peak_color), 1)

    for px in range(width):
        idx = int(px / width * n)
        if idx >= n:
            idx = n - 1
        amp = peaks[idx]
        ph = int(amp * mid * 0.92)
        rh = max(1, int(amp * mid * 0.32))
        painter.setPen(pen_rms)
        painter.drawLine(px, mid - rh, px, mid + rh)
        painter.setPen(pen_peak)
        painter.drawLine(px, mid - ph, px, mid - rh)
        painter.drawLine(px, mid + rh, px, mid + ph)
    painter.end()
    return pix
