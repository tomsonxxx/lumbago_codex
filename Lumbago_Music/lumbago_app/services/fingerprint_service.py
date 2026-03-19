"""
Lumbago Music AI — Serwis fingerprintingu (AcoustID)
======================================================
Generuje i wyszukuje fingerpriny audio przez fpcalc + AcoustID API.
"""

import logging
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class FingerprintResult:
    """Wynik fingerprintingu AcoustID."""
    fingerprint: str
    duration: float
    acoustid: Optional[str] = None
    musicbrainz_recording_id: Optional[str] = None
    title: Optional[str] = None
    artist: Optional[str] = None
    score: float = 0.0


class FingerprintService:
    """
    Generuje fingerprint audio przez fpcalc i wyszukuje w AcoustID.

    Wymaga: bundled/fpcalc/fpcalc.exe lub fpcalc w PATH.
    """

    def __init__(self) -> None:
        from lumbago_app.core.config import get_settings
        settings = get_settings()
        self._fpcalc = settings.FPCALC_PATH
        self._api_key = settings.ACOUSTID_API_KEY

    def generate(self, file_path: Path) -> FingerprintResult:
        """
        Generuje fingerprint pliku audio.

        Args:
            file_path: Ścieżka do pliku.

        Returns:
            FingerprintResult z fingerprint i duration.

        Raises:
            FingerprintError: Jeśli fpcalc niedostępny lub błąd.
        """
        from lumbago_app.core.exceptions import FingerprintError

        fpcalc_path = self._find_fpcalc()
        if not fpcalc_path:
            raise FingerprintError(
                "fpcalc nie znaleziony. Pobierz z: https://acoustid.org/chromaprint"
            )

        try:
            result = subprocess.run(
                [str(fpcalc_path), "-json", str(file_path)],
                capture_output=True, text=True, timeout=30,
            )
            if result.returncode != 0:
                raise FingerprintError(f"fpcalc błąd: {result.stderr}")

            import json
            data = json.loads(result.stdout)
            return FingerprintResult(
                fingerprint=data["fingerprint"],
                duration=data["duration"],
            )
        except subprocess.TimeoutExpired as exc:
            raise FingerprintError("fpcalc timeout po 30s") from exc
        except Exception as exc:
            raise FingerprintError(f"Błąd fpcalc: {exc}") from exc

    def lookup(self, fp_result: FingerprintResult) -> FingerprintResult:
        """
        Wyszukuje fingerprint w AcoustID API.

        Args:
            fp_result: Wynik z generate().

        Returns:
            FingerprintResult uzupełniony o acoustid_id i MusicBrainz ID.

        Raises:
            AcoustidError: Przy błędzie API lub brak klucza.
        """
        raise NotImplementedError(
            "FingerprintService.lookup() — do implementacji w FAZIE 2.\n"
            "Plan: 1) pyacoustid.lookup(), 2) parsuj wyniki, 3) zwróć uzupełniony result."
        )

    def _find_fpcalc(self) -> Optional[Path]:
        """Szuka fpcalc w bundled, PATH i standardowych lokalizacjach."""
        import shutil

        # 1. Bundled
        if self._fpcalc.exists():
            return self._fpcalc

        # 2. PATH
        which = shutil.which("fpcalc")
        if which:
            return Path(which)

        return None
