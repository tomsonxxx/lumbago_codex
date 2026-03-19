"""Lumbago Music AI — Integracja Spotify."""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class SpotifyService:
    """Pobiera Audio Features i metadane ze Spotify API przez spotipy."""

    def get_audio_features(self, spotify_track_id: str) -> Optional[dict]:
        """
        Pobiera Audio Features ze Spotify.

        Returns:
            Dict z: danceability, energy, key, loudness, tempo, valence, ...
        """
        raise NotImplementedError(
            "SpotifyService.get_audio_features() — do implementacji w FAZIE 2.\n"
            "Plan: spotipy.Spotify(auth_manager=...).audio_features([track_id])."
        )

    def search_track(self, artist: str, title: str) -> Optional[dict]:
        """Wyszukuje utwór na Spotify. Zwraca dict z id, popularity itp."""
        raise NotImplementedError
