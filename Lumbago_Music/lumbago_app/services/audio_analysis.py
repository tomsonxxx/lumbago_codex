"""
Lumbago Music AI — Analiza audio (librosa)
============================================
BPM, tonacja, stabilność rytmu.
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class AudioAnalysisResult:
    """Wynik analizy audio jednego pliku."""
    bpm: Optional[float] = None
    bpm_stable: bool = False
    key_musical: Optional[str] = None
    key_camelot: Optional[str] = None
    duration: Optional[float] = None
    sample_rate: Optional[int] = None
    channels: Optional[int] = None
    bit_rate: Optional[int] = None
    codec: Optional[str] = None


class AudioAnalyzer:
    """
    Analizator audio używający librosa.

    Obsługuje: BPM detection, key detection, metadane techniczne.
    """

    def __init__(self) -> None:
        self._logger = logging.getLogger(__name__)

    def analyze(self, file_path: Path) -> AudioAnalysisResult:
        """
        Analizuje plik audio.

        Args:
            file_path: Ścieżka do pliku.

        Returns:
            AudioAnalysisResult z wypełnionymi polami.

        Raises:
            AudioAnalysisError: Przy błędzie librosa.
            FileReadError: Jeśli plik niedostępny.
        """
        from lumbago_app.core.exceptions import AudioAnalysisError, FileReadError

        if not file_path.exists():
            raise FileReadError(f"Plik nie istnieje: {file_path}")

        result = AudioAnalysisResult()

        # Metadane techniczne (mutagen — szybkie, bez dekodowania)
        try:
            result = self._extract_technical_metadata(file_path, result)
        except Exception as exc:
            self._logger.warning("Błąd metadanych mutagen dla %s: %s", file_path.name, exc)

        # Analiza audio (librosa — wolniejsza)
        try:
            result = self._analyze_with_librosa(file_path, result)
        except Exception as exc:
            raise AudioAnalysisError(
                f"Błąd analizy librosa dla {file_path.name}: {exc}"
            ) from exc

        return result

    def _extract_technical_metadata(
        self, file_path: Path, result: AudioAnalysisResult
    ) -> AudioAnalysisResult:
        """Wyciąga metadane techniczne używając mutagen."""
        import mutagen
        audio = mutagen.File(str(file_path), easy=False)
        if audio is None:
            return result

        result.duration = getattr(audio.info, "length", None)
        result.sample_rate = getattr(audio.info, "sample_rate", None)
        result.channels = getattr(audio.info, "channels", None)
        result.bit_rate = getattr(audio.info, "bitrate", None)
        result.codec = type(audio).__name__

        return result

    def _analyze_with_librosa(
        self, file_path: Path, result: AudioAnalysisResult
    ) -> AudioAnalysisResult:
        """Analizuje BPM i tonację używając librosa."""
        import numpy as np

        try:
            import librosa
        except ImportError as exc:
            raise ImportError("librosa nie jest zainstalowane") from exc

        from lumbago_app.core.config import get_settings
        settings = get_settings()

        # Wczytaj audio (mono, 22050 Hz — balans jakość/szybkość)
        y, sr = librosa.load(
            str(file_path),
            sr=22050,
            mono=True,
            duration=120.0,  # Analizuj pierwsze 2 minuty
        )

        # BPM
        tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
        raw_bpm = float(tempo[0]) if hasattr(tempo, '__len__') else float(tempo)

        from lumbago_app.core.utils import normalize_bpm
        result.bpm = normalize_bpm(raw_bpm, settings.BPM_MIN, settings.BPM_MAX)

        # Ocena stabilności rytmu
        if len(beat_frames) > 4:
            intervals = np.diff(beat_frames)
            cv = float(np.std(intervals) / np.mean(intervals))
            result.bpm_stable = cv < 0.05  # CV < 5% = stabilny
        else:
            result.bpm_stable = False

        # Tonacja (Chroma-based)
        result.key_musical = self._detect_key(y, sr)
        if result.key_musical:
            from lumbago_app.core.utils import key_to_camelot
            result.key_camelot = key_to_camelot(result.key_musical)

        self._logger.debug(
            "Analiza %s: BPM=%.1f, key=%s, stable=%s",
            file_path.name, result.bpm or 0,
            result.key_musical, result.bpm_stable,
        )
        return result

    def _detect_key(self, y: object, sr: int) -> Optional[str]:
        """
        Wykrywa tonację używając korelacji z profilami Kruppa.

        Returns:
            Klucz w formacie 'C major' lub None.
        """
        try:
            import librosa
            import numpy as np

            # Chroma Features
            chroma = librosa.feature.chroma_cqt(y=y, sr=sr)  # type: ignore[arg-type]
            chroma_mean = np.mean(chroma, axis=1)

            # Profile Kruppa dla dur i moll
            major_profile = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09,
                                       2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
            minor_profile = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53,
                                       2.54, 4.75, 3.98, 2.69, 3.34, 3.17])

            note_names = ["C", "C#", "D", "Eb", "E", "F",
                          "F#", "G", "Ab", "A", "Bb", "B"]

            best_score = -1.0
            best_key = ""
            for i in range(12):
                rotated = np.roll(chroma_mean, -i)
                # Korelacja z profilem dur
                maj_corr = float(np.corrcoef(rotated, major_profile)[0, 1])
                if maj_corr > best_score:
                    best_score = maj_corr
                    best_key = f"{note_names[i]} major"
                # Korelacja z profilem moll
                min_corr = float(np.corrcoef(rotated, minor_profile)[0, 1])
                if min_corr > best_score:
                    best_score = min_corr
                    best_key = f"{note_names[i]} minor"

            return best_key if best_key else None
        except Exception as exc:
            logger.debug("Błąd wykrywania tonacji: %s", exc)
            return None
