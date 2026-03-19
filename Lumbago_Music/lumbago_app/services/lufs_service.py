"""
Lumbago Music AI — Serwis pomiaru LUFS
=========================================
Pomiar głośności LUFS/LKFS (EBU R128) przez pyloudnorm.
"""

import logging
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class LUFSResult:
    """Wynik pomiaru głośności."""
    integrated_lufs: float
    true_peak_dbfs: float
    lra: float = 0.0   # Loudness Range (LU)
    momentary_max: float = 0.0


class LUFSService:
    """Mierzy głośność pliku audio zgodnie z EBU R128."""

    def measure(self, file_path: Path) -> LUFSResult:
        """
        Mierzy LUFS Integrated i True Peak.

        Args:
            file_path: Ścieżka do pliku audio.

        Returns:
            LUFSResult z wynikami pomiaru.

        Raises:
            AudioAnalysisError: Przy błędzie pomiaru.
        """
        raise NotImplementedError(
            "LUFSService.measure() — do implementacji w FAZIE 2.\n"
            "Plan: 1) wczytaj przez pydub/soundfile, 2) pyloudnorm.Meter(rate).integrated_loudness(),\n"
            "3) true_peak przez pyloudnorm lub ffmpeg, 4) zwróć LUFSResult."
        )

    def gain_to_target(self, current_lufs: float, target_lufs: float = -14.0) -> float:
        """
        Oblicza wymagany gain w dB do osiągnięcia target LUFS.

        Args:
            current_lufs: Zmierzone LUFS.
            target_lufs: Docelowe LUFS (domyślnie -14 LUFS streaming).

        Returns:
            Gain w dB (dodatni = wzmocnienie, ujemny = tłumienie).
        """
        return target_lufs - current_lufs
