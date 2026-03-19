"""
Lumbago Music AI — Scalanie metadanych z wielu źródeł
=======================================================
Łączy wyniki z MusicBrainz, Discogs, Spotify i Last.fm w jeden spójny zestaw.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class MetadataMerger:
    """
    Scala metadane z wielu zewnętrznych serwisów.

    Priorytety (malejące):
    1. Discogs — label, catalog, year dla wydań DJ
    2. MusicBrainz — ISRC, oficjalne ID
    3. Spotify — Audio Features (BPM, key, energy)
    4. Last.fm — tagi społecznościowe
    """

    def merge(
        self,
        track_id: int,
        musicbrainz: Optional[dict] = None,
        discogs: Optional[dict] = None,
        spotify: Optional[dict] = None,
        lastfm_tags: Optional[list[str]] = None,
    ) -> dict:
        """
        Scala metadane do jednego słownika gotowego do zapisu do TrackOrm.

        Args:
            track_id: ID utworu (do logowania).
            musicbrainz: Dane z MusicBrainzService.
            discogs: Dane z DiscogsService.
            spotify: Dane z SpotifyService.get_audio_features().
            lastfm_tags: Tagi z LastFmService.

        Returns:
            Słownik pól TrackOrm do aktualizacji.
        """
        raise NotImplementedError(
            "MetadataMerger.merge() — do implementacji w FAZIE 2.\n"
            "Plan: 1) zdefiniuj priorytety pól, 2) wypełnij słownik wynikowy\n"
            "zachowując pierwszeństwo serwisu o wyższym priorytecie."
        )
