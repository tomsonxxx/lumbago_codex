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


@dataclass
class RgbWaveformBands:
    """Pasmowe piki do waveformy RGB (Rekordbox-style): low / mid / high + composite."""

    low: list[float] = field(default_factory=list)
    mid: list[float] = field(default_factory=list)
    high: list[float] = field(default_factory=list)
    peak: list[float] = field(default_factory=list)

    def as_dict(self) -> dict[str, list[float]]:
        return {"low": self.low, "mid": self.mid, "high": self.high, "peak": self.peak}


def extract_rgb_peaks(audio_path: str | Path, num_points: int = 900) -> RgbWaveformBands:
    """
    Wyciąga pasmowe peaki [0..1] do kolorowej waveformy (bas/środek/góra).
    librosa: FFT per segment; fallback: heurystyka z composite peak.
    """
    composite = extract_peaks(audio_path, num_points=num_points)
    path = Path(audio_path)
    if not path.exists() or not composite:
        return _rgb_from_composite(composite, num_points)

    if _HAS_LIBROSA and _librosa is not None and _np is not None:
        try:
            import warnings

            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                y, sr = _librosa.load(str(path), sr=22050, mono=True)
            if len(y) == 0:
                return _rgb_from_composite(composite, num_points)

            segment_length = max(1, len(y) // num_points)
            low: list[float] = []
            mid: list[float] = []
            high: list[float] = []
            for i in range(num_points):
                start = i * segment_length
                end = min((i + 1) * segment_length, len(y))
                segment = y[start:end]
                if len(segment) < 8:
                    low.append(0.0)
                    mid.append(0.0)
                    high.append(0.0)
                    continue
                spectrum = _np.abs(_np.fft.rfft(segment))
                freqs = _np.fft.rfftfreq(len(segment), 1.0 / sr)
                # Podział zbliżony do Rekordbox RGB (bas / środek / góra)
                lo_e = float(_np.sum(spectrum[freqs < 300]))
                mid_e = float(_np.sum(spectrum[(freqs >= 300) & (freqs < 5000)]))
                hi_e = float(_np.sum(spectrum[freqs >= 5000]))
                low.append(lo_e)
                mid.append(mid_e)
                high.append(hi_e)

            def _norm_band(vals: list[float]) -> list[float]:
                m = max(vals) if vals else 1.0
                if m <= 0:
                    return [0.0] * len(vals)
                return [min(1.0, v / m) for v in vals]

            return RgbWaveformBands(
                low=_norm_band(low),
                mid=_norm_band(mid),
                high=_norm_band(high),
                peak=composite,
            )
        except Exception:
            pass

    return _rgb_from_composite(composite, num_points)


def _rgb_from_composite(peaks: list[float], num_points: int) -> RgbWaveformBands:
    """Heurystyczny podział RGB gdy brak librosa — wygładzenie = bas, reszta = góra."""
    n = len(peaks) or num_points
    if not peaks:
        peaks = _generate_fallback_peaks(n)
    window = max(3, n // 48)
    low: list[float] = []
    mid: list[float] = []
    high: list[float] = []
    for i in range(n):
        lo_i = max(0, i - window)
        hi_i = min(n, i + window + 1)
        smooth = sum(peaks[lo_i:hi_i]) / (hi_i - lo_i)
        transient = max(0.0, peaks[i] - smooth * 0.82)
        low.append(min(1.0, smooth * 0.95))
        mid.append(min(1.0, peaks[i] * 0.88))
        high.append(min(1.0, transient * 1.35 + peaks[i] * 0.25))
    return RgbWaveformBands(low=low, mid=mid, high=high, peak=list(peaks))


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


# Band codes for DJ waveform color coding:
# 0=kick/bass, 1=percussion, 2=vocal/mid, 3=breakdown/quiet
BAND_KICK = 0
BAND_PERC = 1
BAND_VOCAL = 2
BAND_BREAKDOWN = 3


def get_band_tint(band: int) -> QtGui.QColor:
    """Return discrete per-band tint QColor for waveform painting.
    Use together with classify_band_from_ratios() and extract_spectral_bands().
    0=kick/bass (red), 1=perc (yellow), 2=vocal/mid (teal/green), 3=breakdown (blue).
    Fallback neutral. Preserves RGB path in callers.
    Per SZPIEG research 2026-07-14 plan rozbudowy Faza2 (waveform color, advanced Smart, playlist intelligence)... must document identical.
    EFEKT: discrete tint per classify band for visual energy cues in waveform (FILE meta/analiza, STREAM display only).
    """
    tints = {
        BAND_KICK: QtGui.QColor("#e63939"),      # red kick/bass
        BAND_PERC: QtGui.QColor("#e9c46a"),      # yellow/orange perc
        BAND_VOCAL: QtGui.QColor("#2a9d8f"),     # teal/green vocal/mid
        BAND_BREAKDOWN: QtGui.QColor("#457b9d"), # blue breakdown/quiet
    }
    return tints.get(int(band) if band is not None else 3, QtGui.QColor("#888888"))


def classify_band_from_ratios(low: float, mid: float, high: float) -> int:
    """Classify spectral energy into one of four DJ waveform bands."""
    total = low + mid + high
    if total <= 0.05:
        return BAND_BREAKDOWN
    low_r = low / total
    mid_r = mid / total
    high_r = high / total
    if low_r >= 0.45:
        return BAND_KICK
    if mid_r >= 0.42:
        return BAND_PERC
    if high_r >= 0.38:
        return BAND_VOCAL
    return BAND_BREAKDOWN


def extract_spectral_bands(audio_path: str | Path, num_points: int = 600) -> list[int]:
    """
    Per-segment spectral band codes aligned with extract_peaks() sampling.
    Uses librosa STFT when available; otherwise derives bands from fallback peaks.
    Per 2026-06-15 continuation "posepuj dalej zgodnie z planem" + Checklist "Waveform Color Coding"
    (kick/bass red, perc yellow, vocal green, breakdown blue) for DJ visual in WaveformWidget.
    """
    path = Path(audio_path)
    if _HAS_LIBROSA and _librosa is not None and _np is not None and path.exists():
        try:
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                y, sr = _librosa.load(str(path), sr=22050, mono=True)
            if len(y) > 0:
                segment_length = max(1, len(y) // num_points)
                bands: list[int] = []
                for i in range(num_points):
                    start = i * segment_length
                    end = min((i + 1) * segment_length, len(y))
                    segment = y[start:end]
                    if len(segment) < 32:
                        bands.append(BAND_BREAKDOWN)
                        continue
                    rms = float(_np.sqrt(_np.mean(segment ** 2)))
                    if rms < 0.01:
                        bands.append(BAND_BREAKDOWN)
                        continue
                    spec = _np.abs(_librosa.stft(segment, n_fft=512, hop_length=len(segment) // 2 + 1))
                    freqs = _librosa.fft_frequencies(sr=sr, n_fft=512)
                    power = spec.mean(axis=1)
                    low = float(power[freqs < 250].sum())
                    mid = float(power[(freqs >= 250) & (freqs < 4000)].sum())
                    high = float(power[freqs >= 4000].sum())
                    bands.append(classify_band_from_ratios(low, mid, high))
                return bands
        except Exception:
            pass

    peaks = extract_peaks(path, num_points=num_points)
    bands = []
    for amp in peaks:
        if amp < 0.18:
            bands.append(BAND_BREAKDOWN)
        elif amp < 0.42:
            bands.append(BAND_VOCAL)
        elif amp < 0.72:
            bands.append(BAND_PERC)
        else:
            bands.append(BAND_KICK)
    return bands


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
