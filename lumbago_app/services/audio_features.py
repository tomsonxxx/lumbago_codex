"""Ekstrakcja cech audio przez librosa dla Lumbago_Music."""
from __future__ import annotations
import json, logging
from pathlib import Path
import numpy as np

logger = logging.getLogger(__name__)
N_MFCC = 20
WAVEFORM_SAMPLES = 2000
ANALYSIS_DURATION_S = 120


class AudioFeatureResult:
    def __init__(self, path: Path):
        self.path = path
        self.tempo: float | None = None
        self.mfcc_json: str = "[]"
        self.spectral_centroid: float | None = None
        self.spectral_rolloff: float | None = None
        self.brightness: float | None = None
        self.roughness: float | None = None
        self.waveform_blob: bytes | None = None


class AudioAnalysisError(Exception):
    pass


class AudioFeatureExtractor:
    def extract(self, path: Path, duration_s: int = ANALYSIS_DURATION_S) -> AudioFeatureResult:
        try:
            import librosa
        except ImportError:
            raise AudioAnalysisError("librosa nie jest zainstalowana")
        result = AudioFeatureResult(path)
        try:
            y, sr = librosa.load(str(path), sr=22050, mono=True, duration=duration_s)
        except Exception as exc:
            raise AudioAnalysisError(f"Błąd wczytywania: {exc}") from exc
        try:
            tempo_arr, _ = librosa.beat.beat_track(y=y, sr=sr)
            result.tempo = float(tempo_arr[0]) if hasattr(tempo_arr, '__len__') else float(tempo_arr)
        except Exception as e:
            logger.warning("BPM error: %s", e)
        try:
            mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=N_MFCC)
            result.mfcc_json = json.dumps([round(float(v), 4) for v in mfcc.mean(axis=1)])
        except Exception as e:
            logger.warning("MFCC error: %s", e)
        try:
            sc = librosa.feature.spectral_centroid(y=y, sr=sr)
            result.spectral_centroid = float(sc.mean())
            result.brightness = min(1.0, result.spectral_centroid / (sr / 2))
        except Exception as e:
            logger.warning("Spectral error: %s", e)
        try:
            sr_arr = librosa.feature.spectral_rolloff(y=y, sr=sr)
            result.spectral_rolloff = float(sr_arr.mean())
        except Exception as e:
            logger.warning("Rolloff error: %s", e)
        try:
            sb = librosa.feature.spectral_bandwidth(y=y, sr=sr)
            result.roughness = min(1.0, float(sb.mean()) / (sr / 2))
        except Exception as e:
            logger.warning("Bandwidth error: %s", e)
        try:
            result.waveform_blob = compute_waveform_blob(y, WAVEFORM_SAMPLES)
        except Exception as e:
            logger.warning("Waveform error: %s", e)
        return result

    def build_ai_prompt_context(self, result: AudioFeatureResult) -> str:
        mfcc = json.loads(result.mfcc_json) if result.mfcc_json else []
        parts = []
        if result.tempo:
            parts.append(f"tempo_bpm={result.tempo:.1f}")
        if result.brightness is not None:
            lvl = "bright" if result.brightness > 0.6 else ("mid" if result.brightness > 0.3 else "dark")
            parts.append(f"brightness={lvl}({result.brightness:.2f})")
        if result.roughness is not None:
            lvl = "rough" if result.roughness > 0.6 else ("moderate" if result.roughness > 0.3 else "smooth")
            parts.append(f"roughness={lvl}({result.roughness:.2f})")
        if mfcc:
            parts.append(f"mfcc_top5={mfcc[:5]}")
        return "[Audio features: " + ", ".join(parts) + "]" if parts else ""


def compute_waveform_blob(y: np.ndarray, n_samples: int = WAVEFORM_SAMPLES) -> bytes:
    if len(y) == 0:
        return b""
    chunk = max(1, len(y) // n_samples)
    peaks = []
    for i in range(n_samples):
        s = i * chunk
        e = min(s + chunk, len(y))
        peaks.append(float(np.max(np.abs(y[s:e]))) if s < len(y) else 0.0)
    return np.array(peaks, dtype=np.float32).tobytes()


def waveform_from_blob(blob: bytes) -> np.ndarray:
    if not blob:
        return np.array([], dtype=np.float32)
    return np.frombuffer(blob, dtype=np.float32).copy()


def compute_waveform_blob_from_file(path: Path, n_samples: int = WAVEFORM_SAMPLES, duration_s: int = ANALYSIS_DURATION_S) -> bytes:
    try:
        import librosa
        y, _ = librosa.load(str(path), sr=22050, mono=True, duration=duration_s)
        return compute_waveform_blob(y, n_samples)
    except Exception as exc:
        logger.warning("Waveform file error %s: %s", path, exc)
        return b""
