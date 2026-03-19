"""
Lumbago Music AI — Serwis generowania setlisty AI
===================================================
Generuje propozycje kolejności utworów na set DJ
z uwzględnieniem harmonii Camelot, BPM i energii.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class SetlistService:
    """
    Generuje AI-assisted setlisty dla DJ setów.

    Algorytm:
    1. Pobiera kandydatów z bazy (filtr gatunku/energii/BPM).
    2. Wysyła listę do LLM z prośbą o ułożenie w optymalnej kolejności.
    3. Waliduje harmoniczność (Camelot) i płynność BPM.
    4. Zwraca posortowaną listę ID i uzasadnienie.
    """

    def __init__(self) -> None:
        from lumbago_app.services.ai.llm_router import get_router
        self._router = get_router()

    def generate_setlist(
        self,
        track_ids: list[int],
        duration_minutes: int = 60,
        energy_curve: str = "build_peak_outro",
        start_key: Optional[str] = None,
        notes: str = "",
    ) -> dict[str, object]:
        """
        Generuje setlistę z listy kandydatów.

        Args:
            track_ids: ID kandydatów do setlisty.
            duration_minutes: Docelowy czas trwania w minutach.
            energy_curve: Typ krzywej energii:
                - "build_peak_outro": buduj → peak → zejście
                - "flat": równa energia przez cały set
                - "random": AI decyduje
            start_key: Opcjonalny klucz startowy (Camelot, np. "8B").
            notes: Dodatkowe instrukcje dla AI.

        Returns:
            {
                "ordered_track_ids": [...],
                "total_duration": float,
                "explanation": str,
                "key_transitions": [...],
                "bpm_curve": [...],
            }

        Raises:
            NoProviderAvailableError: Brak providera AI.
            AIError: Błąd komunikacji z API.
        """
        raise NotImplementedError(
            "SetlistService.generate_setlist() — do implementacji w FAZIE 3.\n"
            "Plan: 1) pobierz metadane track_ids, 2) zbuduj prompt z parametrami setu,\n"
            "3) wywołaj _router.tag_tracks() w trybie setlist, 4) parsuj i waliduj wynik."
        )

    def validate_transitions(self, ordered_ids: list[int]) -> list[dict[str, object]]:
        """
        Sprawdza jakość przejść między kolejnymi utworami.

        Args:
            ordered_ids: Lista ID w kolejności setu.

        Returns:
            Lista ocen przejść: [{"from_id": X, "to_id": Y, "camelot_ok": bool,
            "bpm_delta": float, "energy_delta": int}, ...]
        """
        raise NotImplementedError(
            "SetlistService.validate_transitions() — do implementacji w FAZIE 3."
        )
