"""
Lumbago Music AI — Serwis tagowania AI
=========================================
Orkiestruje tagowanie: LLM Router + Cache + zapis do bazy.
"""

import logging
from typing import Callable, Optional

from lumbago_app.services.ai.llm_cache import LLMCache
from lumbago_app.services.ai.llm_router import get_router

logger = logging.getLogger(__name__)

# Callback postępu: (current, total, track_title) -> None
ProgressCallback = Callable[[int, int, str], None]


class TaggerService:
    """
    Serwis AI tagowania utworów.

    Przepływ:
    1. Pobiera metadane z bazy dla wybranych ID.
    2. Sprawdza cache (pomija już otagowane).
    3. Wysyła do LLM Router (najtańszy dostępny provider).
    4. Zapisuje wyniki do bazy (genre, mood, style, energy, tags).
    5. Raportuje postęp przez callback.
    """

    def __init__(self, batch_size: int = 20) -> None:
        """
        Args:
            batch_size: Liczba utworów na jedno zapytanie LLM.
        """
        self.batch_size = batch_size
        self._router = get_router()

    def tag_tracks(
        self,
        track_ids: list[int],
        progress_callback: Optional[ProgressCallback] = None,
        use_cache: bool = True,
    ) -> dict[int, bool]:
        """
        Taguje podane utwory.

        Args:
            track_ids: Lista ID utworów z bazy.
            progress_callback: Opcjonalny callback postępu.
            use_cache: Czy używać cache LLM.

        Returns:
            Słownik track_id -> sukces (True/False).
        """
        from lumbago_app.core.exceptions import NoProviderAvailableError
        from lumbago_app.data.database import session_scope
        from lumbago_app.data.models import TagOrm, TrackOrm

        results: dict[int, bool] = {tid: False for tid in track_ids}
        total = len(track_ids)

        if not self._router.has_providers:
            logger.warning("Brak providerów AI — tagowanie niemożliwe")
            return results

        # Przetwarzaj w batchach
        for batch_start in range(0, total, self.batch_size):
            batch_ids = track_ids[batch_start: batch_start + self.batch_size]

            try:
                with session_scope() as session:
                    # Pobierz metadane
                    tracks = [
                        session.get(TrackOrm, tid)
                        for tid in batch_ids
                        if session.get(TrackOrm, tid)
                    ]
                    tracks_meta = [
                        {
                            "id": t.id,
                            "title": t.title or "",
                            "artist": t.artist or "",
                            "album": t.album or "",
                            "genre": t.genre or "",
                            "bpm": t.bpm,
                            "key": t.key_camelot or t.key_musical or "",
                            "duration": t.duration,
                        }
                        for t in tracks
                    ]

                    if not tracks_meta:
                        continue

                    # Sprawdź cache
                    tag_results = None
                    provider_name = (
                        self._router.get_cheapest().provider_name
                        if self._router.get_cheapest()
                        else "unknown"
                    )
                    cache = LLMCache(provider_name)
                    if use_cache:
                        tag_results = cache.get(tracks_meta)

                    # Wywołaj LLM jeśli brak cache
                    if tag_results is None:
                        tag_results = self._router.tag_tracks(tracks_meta)
                        if use_cache:
                            cache.set(tracks_meta, tag_results)

                    # Zapisz wyniki
                    for track in tracks:
                        track_result = tag_results.get(track.id) or tag_results.get(str(track.id))
                        if not track_result:
                            continue

                        # Aktualizuj pola
                        if genre := track_result.get("genre"):
                            track.genre = genre
                        if style := track_result.get("style"):
                            track.style = style
                        if energy := track_result.get("energy_level"):
                            track.energy_level = int(energy)
                        if moods := track_result.get("mood"):
                            import json
                            track.mood = json.dumps(moods, ensure_ascii=False)

                        # Dodaj tagi
                        for tag_name in track_result.get("tags", []):
                            existing = any(t.name == tag_name for t in track.tags)
                            if not existing:
                                track.tags.append(
                                    TagOrm(
                                        name=tag_name,
                                        category="ai",
                                        source="ai",
                                        confidence=track_result.get("confidence", 0.8),
                                    )
                                )

                        results[track.id] = True

                        # Callback postępu
                        if progress_callback:
                            current = batch_start + tracks.index(track) + 1
                            progress_callback(current, total, track.title or str(track.id))

            except NoProviderAvailableError:
                logger.error("Brak dostępnych providerów AI")
                break
            except Exception as exc:
                logger.error("Błąd podczas tagowania batcha %d: %s", batch_start, exc)

        success_count = sum(1 for v in results.values() if v)
        logger.info("Tagowanie zakończone: %d/%d sukces", success_count, total)
        return results

    def estimate_cost(self, track_count: int) -> dict[str, float]:
        """Szacuje koszt tagowania dla podanej liczby utworów."""
        return self._router.estimate_cost(track_count)
