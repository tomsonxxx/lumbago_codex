"""
Lumbago Music AI — Serwis generowania waveform
================================================
Generuje dane szczytu fali (peaks) dla wizualizacji.
"""

import json
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class WaveformService:
    """Generuje dane waveform (peaks) dla widgetu wizualizacji."""

    def __init__(self, resolution: int = 1000) -> None:
        """
        Args:
            resolution: Liczba próbek (słupków) w waveformie.
        """
        self.resolution = resolution

    def generate(self, file_path: Path) -> Optional[str]:
        """
        Generuje dane waveform jako JSON string.

        Args:
            file_path: Ścieżka do pliku audio.

        Returns:
            JSON string z listą floatów 0.0-1.0 lub None przy błędzie.
        """
        raise NotImplementedError(
            "WaveformService.generate() — do implementacji w FAZIE 2.\n"
            "Plan: 1) wczytaj przez librosa/pydub, 2) resample do resolution,\n"
            "3) oblicz RMS per chunk, 4) normalizuj 0-1, 5) zakoduj JSON."
        )

    def generate_stereo(self, file_path: Path) -> Optional[str]:
        """
        Generuje dane waveform dla obu kanałów (stereo).

        Returns:
            JSON: {"left": [...], "right": [...]}
        """
        raise NotImplementedError(
            "WaveformService.generate_stereo() — do implementacji w FAZIE 2."
        )

    def peaks_from_json(self, json_str: str) -> list[float]:
        """Deserializuje peaks z JSON stringa."""
        try:
            data = json.loads(json_str)
            if isinstance(data, list):
                return data
            if isinstance(data, dict) and "left" in data:
                return data["left"]
            return []
        except (json.JSONDecodeError, KeyError):
            return []
