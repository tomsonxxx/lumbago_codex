"""
Pakiet ui.dj – komponenty DJ w stylu Rekordbox dla Lumbago Music AI.

Zawiera kontroler decków oraz widoki prezentacyjne.
Wszystkie komunikaty i komentarze po polsku.
"""

from __future__ import annotations

# Re-eksporty (bezpieczne – nie importują ciężkich zależności przy starcie)
from ui.dj.deck_controller import DeckController
from ui.dj.styles import BOOTH_COLORS, get_value_label_stylesheet
from ui.dj.hotcue_manager import HotcueManager, format_track_time  # CZysty moduł – brak cyklu z dj_player_window

# Małe widgety (szkielety w tej iteracji)
from ui.dj.views.hotcue_pad import HotcuePad
from ui.dj.views.hotcue_grid import HotcuePadGrid
from ui.dj.views.transport_bar import TransportBar
from ui.dj.views.pitch_control import PitchControl
from ui.dj.views.eq_strip import EQStrip

# Publiczne API pakietu
__all__ = [
    "DeckController",
    "BOOTH_COLORS",
    "get_value_label_stylesheet",
    "HotcueManager",
    "format_track_time",
    "HotcuePad",
    "HotcuePadGrid",
    "TransportBar",
    "PitchControl",
    "EQStrip",
]
