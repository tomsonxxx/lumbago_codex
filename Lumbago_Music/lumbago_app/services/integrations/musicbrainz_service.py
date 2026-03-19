"""
Lumbago Music AI — Integracja MusicBrainz
==========================================
Wyszukuje metadane przez MusicBrainz API.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class MusicBrainzService:
    """Pobiera metadane z MusicBrainz API przez musicbrainzngs."""

    def __init__(self) -> None:
        from lumbago_app.core.config import get_settings
        settings = get_settings()
        try:
            import musicbrainzngs
            musicbrainzngs.set_useragent(
                "Lumbago Music", "1.0", "https://github.com/lumbago/music"
            )
            musicbrainzngs.set_rate_limit(settings.MUSICBRAINZ_RATE_LIMIT)
            self._mb = musicbrainzngs
        except ImportError:
            logger.warning("musicbrainzngs nie zainstalowane")
            self._mb = None

    def search_recording(
        self,
        artist: str,
        title: str,
        duration_seconds: Optional[float] = None,
    ) -> Optional[dict]:
        """
        Wyszukuje nagranie w MusicBrainz.

        Args:
            artist: Artysta.
            title: Tytuł.
            duration_seconds: Czas trwania do zawężenia wyników.

        Returns:
            Słownik z metadanymi lub None.

        Raises:
            MusicBrainzError: Przy błędzie API.
        """
        raise NotImplementedError(
            "MusicBrainzService.search_recording() — do implementacji w FAZIE 2.\n"
            "Plan: 1) musicbrainzngs.search_recordings(artist=..., recording=...),\n"
            "2) dopasuj po duration, 3) pobierz label/catalog/isrc, 4) zwróć dict."
        )

    def get_by_id(self, recording_id: str) -> Optional[dict]:
        """Pobiera pełne dane nagrania po MusicBrainz Recording ID."""
        raise NotImplementedError(
            "MusicBrainzService.get_by_id() — do implementacji w FAZIE 2."
        )
