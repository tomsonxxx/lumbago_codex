"""Lumbago Music AI — Integracja Last.fm."""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class LastFmService:
    """Pobiera tagi i scrobble z Last.fm API przez pylast."""

    def get_track_tags(self, artist: str, title: str) -> list[str]:
        """Pobiera popularne tagi dla utworu z Last.fm."""
        raise NotImplementedError(
            "LastFmService.get_track_tags() — do implementacji w FAZIE 2.\n"
            "Plan: pylast.LastFMNetwork(api_key=...).get_track(artist, title).get_top_tags()."
        )

    def scrobble(self, artist: str, title: str, timestamp: Optional[int] = None) -> bool:
        """Scrobbluje utwór do Last.fm. Zwraca True jeśli sukces."""
        raise NotImplementedError(
            "LastFmService.scrobble() — do implementacji w FAZIE 3."
        )
