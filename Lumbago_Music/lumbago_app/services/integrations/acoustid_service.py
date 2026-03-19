"""Lumbago Music AI — Integracja AcoustID."""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class AcoustIDService:
    """Wyszukuje metadane przez AcoustID fingerprint lookup."""

    def lookup(self, fingerprint: str, duration: float) -> Optional[dict]:
        """
        Wyszukuje nagranie po fingerprinie.

        Returns:
            Słownik {"acoustid": str, "recording_id": str, "score": float} lub None.

        Raises:
            AcoustidError: Przy błędzie API.
        """
        raise NotImplementedError(
            "AcoustIDService.lookup() — do implementacji w FAZIE 2.\n"
            "Plan: pyacoustid.lookup(api_key, fingerprint, duration, meta='recordings')."
        )
