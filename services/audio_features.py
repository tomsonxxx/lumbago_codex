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
            logger.error("[problematic-audio] load_failed path=%s error=%s", path, exc)
            raise AudioAnalysisError(f"Błąd wczytywania: {exc}") from exc
        try:
            tempo_arr, _ = librosa.beat.beat_track(y=y, sr=sr)
            result.tempo = float(tempo_arr[0]) if hasattr(tempo_arr, '__len__') else float(tempo_arr)
        except Exception as e:
            logger.warning("BPM error for %s: %s", path.name, e)
        try:
            mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=N_MFCC)
            result.mfcc_json = json.dumps([round(float(v), 4) for v in mfcc.mean(axis=1)])
        except Exception as e:
            logger.warning("MFCC error for %s: %s", path.name, e)
        try:
            sc = librosa.feature.spectral_centroid(y=y, sr=sr)
            result.spectral_centroid = float(sc.mean())
            result.brightness = min(1.0, result.spectral_centroid / (sr / 2))
        except Exception as e:
            logger.warning("Spectral error for %s: %s", path.name, e)
        try:
            sr_arr = librosa.feature.spectral_rolloff(y=y, sr=sr)
            result.spectral_rolloff = float(sr_arr.mean())
        except Exception as e:
            logger.warning("Rolloff error for %s: %s", path.name, e)
        try:
            sb = librosa.feature.spectral_bandwidth(y=y, sr=sr)
            result.roughness = min(1.0, float(sb.mean()) / (sr / 2))
        except Exception as e:
            logger.warning("Bandwidth error for %s: %s", path.name, e)
        try:
            result.waveform_blob = compute_waveform_blob(y, WAVEFORM_SAMPLES)
        except Exception as e:
            logger.warning("Waveform error for %s: %s", path.name, e)
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


# ============================================================
# Playlist intelligence sort helpers (Faza2)
# harmonic Camelot + energy flow. Per SZPIEG research 2026-07-14 plan rozbudowy Faza2 (waveform color, advanced Smart, playlist intelligence)... must document identical.
# EFEKT (playlist intel): auto sort helpers -> used in order dialog for better mix flow (meta only, no file mods).
# ============================================================

_CAMELOT_WHEEL = ["1A","1B","2A","2B","3A","3B","4A","4B","5A","5B","6A","6B",
                  "7A","7B","8A","8B","9A","9B","10A","10B","11A","11B","12A","12B"]

def camelot_distance(k1: str | None, k2: str | None) -> int:
    """Harmonic distance on Camelot wheel. 0 = identical key, lower = more compatible for mixing."""
    if not k1 or not k2:
        return 99
    a = k1.strip().upper()
    b = k2.strip().upper()
    if a == b:
        return 0
    if a not in _CAMELOT_WHEEL or b not in _CAMELOT_WHEEL:
        return 12
    ia = _CAMELOT_WHEEL.index(a)
    ib = _CAMELOT_WHEEL.index(b)
    # wheel distance + letter compat
    d = min(abs(ia - ib), 24 - abs(ia - ib)) // 2
    # prefer same letter or +1/-1
    la, lb = a[-1], b[-1]
    if la == lb:
        return d
    if (la == "A" and lb == "B") or (la == "B" and lb == "A"):
        return max(1, d)
    return d + 1

def sort_tracks_for_harmonic_mixing(tracks: list, start_key: str | None = None) -> list:
    """Sort tracks for smooth harmonic progression (Camelot wheel order). Uses track.key . Fallback stable."""
    if not tracks:
        return tracks
    key_get = lambda t: getattr(t, "key", None) or getattr(t, "camelot", None)
    if start_key is None:
        start_key = key_get(tracks[0])
    remaining = list(tracks)
    ordered = []
    curr = start_key
    while remaining:
        # pick closest to curr
        best = min(remaining, key=lambda t: camelot_distance(curr, key_get(t)))
        ordered.append(best)
        remaining.remove(best)
        curr = key_get(best) or curr
    return ordered

def sort_tracks_by_energy(tracks: list, ascending: bool = False) -> list:
    """Sort by energy (high to low by default for energy build-up sets)."""
    def en(t):
        e = getattr(t, "energy", None)
        return e if e is not None else -1
    return sorted(tracks, key=en, reverse=not ascending)


# Faza5 starter (per NOWA_LISTA 2026-07-14 items 21-24 + PLAN_MASTER)
# Crate digger / find similar using audio features (mfcc, energy, key, brightness...).
# Real impl: cosine / euclid dist na wektorach + filtr key/energy. Stub teraz.
def find_similar_crate_digger(
    seed_track: Any,
    candidate_tracks: list,
    top_k: int = 10,
    prefer_harmonic: bool = True
) -> list:
    """Faza5: znajdź podobne utwory do seed (crate digger). Używa energy/key + features z DB.
    Na razie zwraca puste lub proste sort — pełne w późniejszej fazie.
    Per SZPIEG research 2026-07-14 plan rozbudowy Faza5 + 'dalej az do ukonczenia' ... must document identical.
    """
    # Minimal starter: sort by energy closeness if available (placeholder)
    if not candidate_tracks:
        return []
    try:
        seed_e = getattr(seed_track, "energy", None) or 0.5
        def score(t):
            e = getattr(t, "energy", None) or 0.5
            return abs(e - seed_e)
        sorted_c = sorted(candidate_tracks, key=score)
        return sorted_c[:top_k]
    except Exception:
        return candidate_tracks[:top_k]

# Blok 5 additional note (transition): multi-monitor/booth advanced support notes in styles/BOOTH + helper. Advanced cue/memory in hotcue tests. Performance via prior large lib sims. Per fraza for Faza5.
