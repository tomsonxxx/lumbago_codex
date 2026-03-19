"""Lumbago Music AI — Integracja Discogs."""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class DiscogsService:
    """Pobiera metadane wydania z Discogs API."""

    def search(self, artist: str, title: str) -> Optional[dict]:
        """Wyszukuje wydanie na Discogs. Zwraca dict lub None."""
        raise NotImplementedError(
            "DiscogsService.search() — do implementacji w FAZIE 2.\n"
            "Plan: discogs_client.Client().search(artist+' '+title, type='release')."
        )

    def get_release(self, release_id: str) -> Optional[dict]:
        """Pobiera szczegóły wydania po Discogs Release ID."""
        raise NotImplementedError
