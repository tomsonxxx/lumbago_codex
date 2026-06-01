"""
Pakiet ui.dj.views – małe, wielokrotnego użytku widgety DJ (booth-first).

Widoki prezentacyjne (dumb views) łączą się z DeckController przez sygnały.
Zero logiki biznesowej tutaj.
"""

from __future__ import annotations

from .hotcue_pad import HotcuePad
from .hotcue_grid import HotcuePadGrid
from .transport_bar import TransportBar
from .pitch_control import PitchControl
from .eq_strip import EQStrip
from .mixer_strip import MixerStrip
from .memory_controls import MemoryControls

# Główne widoki prezentacyjne (Front A – zakończony)
from .focused_deck_view import FocusedDeckView
from .console_deck_view import ConsoleDeckView
from .dual_console_widget import DualConsoleWidget

__all__ = [
    "HotcuePad",
    "HotcuePadGrid",
    "TransportBar",
    "PitchControl",
    "EQStrip",
    "MixerStrip",
    "MemoryControls",
    # Nowe widoki dumb (zgodne z AGENT 3)
    "FocusedDeckView",
    "ConsoleDeckView",
    "DualConsoleWidget",
]
