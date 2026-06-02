"""
ui/dj/hotcue_manager.py

Czysta, wyodrębniona warstwa zarządzania hotcue'ami (dane + persystencja w DB).

PRZENIESIONE z ui/dj_player_window.py (faza final cleanup AGENT3 + parallel).

Cele:
- Usunięcie ryzyka cyklu importów (deck_controller.py importował z monstrualnego pliku)
- Czysty re-eksport bez zależności od dj_player_window
- Pełna kompatybilność z DeckController (nowa architektura)
- Użycie centralnej palety BOOTH_COLORS (zamiast lokalnego COLORS)

HotcueManager jest UI-agnostyczny. Nie wykonuje snapów ani seeków – to zadanie właściciela (kontrolera/widoku).

Format track time też tu (wspólny czysty helper).

Wszystkie komentarze i docstringi po polsku + kluczowe angielskie dla czytelności.
"""

from __future__ import annotations

import logging
from typing import Any

from core.models import CuePoint

# ------------------------------------------------------------------
# Self-contained import repo cue points (persystencja DB)
# Niezależny od dj_player_window – zero ryzyka cyklu.
# ------------------------------------------------------------------
try:
    from data.repository import (
        get_cue_points_for_track,
        save_cue_point,
        delete_cue_point,
    )
    _HAS_CUE_REPOSITORY = True
except ImportError:
    _HAS_CUE_REPOSITORY = False
    get_cue_points_for_track = None
    save_cue_point = None
    delete_cue_point = None

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------
# REFACTOR: Wspólny czysty helper formatowania czasu
# Wyodrębniony z duplikacji (poprzednie DeckWidget / SinglePlayerView / DeckController).
# Pure function – zero side effects, zero Qt.
# ------------------------------------------------------------------

def format_track_time(ms: int | None) -> str:
    """Formatuj czas w milisekundach jako string "m:ss" (zero-padded).

    Args:
        ms: Czas w ms lub None.

    Returns:
        "m:ss" lub "0:00" dla None/ujemnych.
    """
    if ms is None:
        return "0:00"
    total_sec = max(0, int(ms)) // 1000
    m = total_sec // 60
    s = total_sec % 60
    return f"{m}:{s:02d}"


# ------------------------------------------------------------------
# Import palety BOOTH po zdefiniowaniu helperów (bezpieczny dla importów)
# Używamy jej do domyślnych kolorów hotcue (8 unikalnych, high-contrast).
# ------------------------------------------------------------------
from ui.dj.styles import BOOTH_COLORS


class HotcueManager:
    """Zarządza przechowywaniem punktów hotcue (index -> time_ms) z opcjonalną persystencją w DB.

    Klasa hermetyzuje model danych i CRUD dla hotcue'ów, dzięki czemu
    DeckWidget (0-7 + tryb 4/8), SinglePlayerView (0-3) oraz nowa architektura
    (DeckController + Focused/Console views) używają identycznej logiki.

    Manager jest UI-agnostyczny – nie robi quantize snap ani playback seek.
    Te operacje zostają w kontrolerze/widoku (zachowanie oryginalne).

    # REFACTOR (final cleanup): Pełne przeniesienie do ui/dj/ w celu eliminacji
    # tymczasowego importu z dj_player_window i ryzyka cyklu.
    # Kolory hotcue pochodzą z BOOTH_COLORS (spójne z nową architekturą).
    """

    def __init__(self, max_cues: int = 8) -> None:
        """Inicjalizuj pusty manager.

        Args:
            max_cues: Górna granica indeksów hotcue (Deck=8, Single=4, clamped [4,8]).
        """
        self._hotcues: dict[int, int] = {}
        self._max_cues: int = max(4, min(max_cues, 8))
        self._track_id: int | None = None

    # ------------------------------------------------------------------
    # Dostęp do danych (używany przez oba stare widoki + nowy DeckController)
    # ------------------------------------------------------------------

    @property
    def hotcues(self) -> dict[int, int]:
        """Zwraca płytką kopię aktualnych hotcue'ów (index -> time_ms)."""
        return dict(self._hotcues)

    def get(self, index: int) -> int | None:
        """Pobierz czas dla konkretnego indeksu hotcue lub None."""
        return self._hotcues.get(index)

    def set(self, index: int, time_ms: int) -> None:
        """Zapisz lub nadpisz hotcue (clamped do [0, max_cues))."""
        if 0 <= index < self._max_cues:
            self._hotcues[index] = int(time_ms)

    def clear(self, index: int) -> None:
        """Usuń hotcue jeśli istnieje."""
        self._hotcues.pop(index, None)

    def clear_all(self) -> None:
        """Wyczyść wszystkie hotcue (używane przy unload/load tracka)."""
        self._hotcues.clear()

    def set_track_id(self, track_id: int | None) -> None:
        """Powiąż managera z ID tracka z DB dla wywołań persystencji."""
        self._track_id = track_id if track_id else None

    def get_visible_cues(self, visible_count: int | None = None) -> dict[int, int]:
        """Zwraca tylko cue których indeks < visible_count (do renderowania padów)."""
        limit = visible_count if visible_count is not None else self._max_cues
        return {k: v for k, v in self._hotcues.items() if 0 <= k < limit}

    # ------------------------------------------------------------------
    # Persystencja DB (centralizacja wcześniej zduplikowanego kodu)
    # ------------------------------------------------------------------

    def load_from_db(self, track_id: int) -> dict[int, int]:
        """Załaduj hotcue dla track_id z repozytorium.

        Zwraca załadowany dict (również zapisany wewnętrznie).
        Cicho zwraca puste na błąd lub brak repo (oryginalne zachowanie).
        """
        self.clear_all()
        self.set_track_id(track_id)

        if not _HAS_CUE_REPOSITORY or not get_cue_points_for_track:
            logger.debug("HotcueManager: No cue repository available")
            return {}

        try:
            cues = get_cue_points_for_track(track_id)
            for cue in cues:
                if cue.hotcue_index is not None and 0 <= cue.hotcue_index < self._max_cues:
                    self._hotcues[cue.hotcue_index] = cue.time_ms
            logger.debug(f"HotcueManager: Loaded {len(self._hotcues)} hotcues for track {track_id}")
        except Exception as e:
            logger.warning(f"HotcueManager: Error loading hotcues: {e}")

        return dict(self._hotcues)

    def save_to_db(self, index: int, time_ms: int, color: str | None = None) -> None:
        """Zapisz pojedynczy hotcue do DB (jeśli repo + track_id dostępne).

        Dokładnie odwzorowuje oryginalną logikę DeckWidget/SinglePlayerView.
        Kolor domyślny z BOOTH_COLORS (8 unikalnych kolorów high-contrast).
        """
        if not self._track_id:
            return
        if not _HAS_CUE_REPOSITORY or not save_cue_point:
            return

        try:
            default_colors = BOOTH_COLORS.get("hotcue", [
                "#ef4444", "#f97316", "#eab308", "#22c55e",
                "#06b6d4", "#3b82f6", "#8b5cf6", "#ec4899"
            ])
            cue = CuePoint(
                time_ms=time_ms,
                cue_type="hotcue",
                hotcue_index=index,
                color=color or default_colors[index % len(default_colors)],
            )
            save_cue_point(self._track_id, cue)
            logger.debug(f"HotcueManager: Saved hotcue {index} ({time_ms}ms)")
        except Exception as e:
            logger.warning(f"HotcueManager: Error saving hotcue {index}: {e}")

    def delete_from_db(self, index: int) -> None:
        """Usuń hotcue z DB (graceful przy braku repo/track)."""
        if not self._track_id:
            return
        if not _HAS_CUE_REPOSITORY or not delete_cue_point:
            return

        try:
            delete_cue_point(self._track_id, hotcue_index=index)
            logger.debug(f"HotcueManager: Deleted hotcue {index} from DB")
        except Exception as e:
            logger.warning(f"HotcueManager: Error deleting hotcue {index}: {e}")


# Publiczne API modułu
__all__ = [
    "HotcueManager",
    "format_track_time",
    "BOOTH_COLORS",  # re-eksport dla wygody (opcjonalnie)
]
