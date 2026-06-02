"""
ui/dj/styles.py

Centralna paleta kolorów i helpery stylesheetów w stylu booth (Rekordbox/Traktor).
Zaprojektowane dla słabego oświetlenia klubu, rękawiczek i szybkiej pracy.

Wszystkie stałe i funkcje wyłącznie po polsku w komentarzach/docstringach.
Używaj tych helperów – ZERO inline stylesheetów w nowych widokach!
"""

from __future__ import annotations

from typing import Any

# ------------------------------------------------------------------
# BOOTH_COLORS – oficjalna paleta z projektu AGENT 3 (Rekordbox-Style Redesign)
# ------------------------------------------------------------------
BOOTH_COLORS: dict[str, Any] = {
    "bg": "#0a0d14",                    # główne tło okna
    "surface": "#12171f",               # panele decków
    "surface_elev": "#1a212c",          # podniesione karty (single mode)
    "border": "#2a3442",
    "border_strong": "#3a4556",
    "text_primary": "#f0f4f8",
    "text_secondary": "#a8b3c2",
    "text_muted": "#6b7688",
    "accent": "#00e0ff",                # cyan (info, BPM, deck labels)
    "accent_orange": "#ff8a00",         # energia, playhead alternatywa
    "play": "#22c55e",
    "stop": "#ef4444",
    "cue": "#f43f5e",
    "loop": "#3b82f6",
    "warning": "#eab308",
    "hotcue": [                         # 8 unikalnych, wysokokontrastowych (Rekordbox style)
        "#ef4444", "#f97316", "#eab308", "#22c55e",
        "#06b6d4", "#3b82f6", "#8b5cf6", "#ec4899"
    ],
    "wave_bg": "#0f141c",
    "wave_peak": "#67e8f9",
    "wave_rms": "#1e3a52",
    "playhead": "#f43f5e",
    "playhead_glow": "#fb7185",
    "sync_active": "#166534",
}

# ------------------------------------------------------------------
# Helpery do generowania stylesheetów (czysta separacja stylów)
# ------------------------------------------------------------------

def get_deck_panel_stylesheet() -> str:
    """Zwraca stylesheet dla głównego panelu decku (surface + border)."""
    c = BOOTH_COLORS
    return f"""
        QFrame#DeckPanel, DeckConsoleView, FocusedDeckView {{
            background-color: {c["surface"]};
            border: 1px solid {c["border"]};
            border-radius: 10px;
        }}
        QFrame#DeckPanel:hover {{
            border-color: {c["border_strong"]};
        }}
    """


def get_hotcue_pad_stylesheet(index: int, has_cue: bool = False) -> str:
    """
    Zwraca kompletny stylesheet dla HotcuePad o danym indeksie (0-7).

    Używa 8 unikalnych kolorów z palety. Obsługuje stany:
    - empty (tylko obramowanie)
    - set (wypełniony kolorem)
    - hover / pressed
    """
    c = BOOTH_COLORS
    color = c["hotcue"][index % len(c["hotcue"])]

    if has_cue:
        # Stan ustawiony – pełne wypełnienie + biały border
        return f"""
            QPushButton {{
                background-color: {color};
                color: {c["bg"]};
                border: 2px solid {c["text_primary"]};
                border-radius: 8px;
                font-weight: 900;
                font-size: 18px;
            }}
            QPushButton:hover {{
                background-color: {c["text_primary"]};
                color: {c["bg"]};
                border-color: {color};
            }}
            QPushButton:pressed {{
                background-color: #e2e8f0;
            }}
        """
    else:
        # Stan pusty – kolorowy border + ciemne tło
        return f"""
            QPushButton {{
                background-color: {c["surface"]};
                color: {color};
                border: 2px solid {color};
                border-radius: 8px;
                font-weight: 800;
                font-size: 18px;
            }}
            QPushButton:hover {{
                background-color: {c["surface_elev"]};
                border-color: {c["text_primary"]};
                color: {c["text_primary"]};
            }}
            QPushButton:pressed {{
                background-color: {color};
                color: {c["bg"]};
            }}
        """


def get_transport_button_stylesheet(role: str = "play") -> str:
    """
    Duże przyciski transport: PLAY, CUE, STOP.
    role: 'play' | 'cue' | 'stop'
    """
    c = BOOTH_COLORS
    if role == "play":
        bg = c["play"]
        hover = "#16a34a"
    elif role == "cue":
        bg = c["cue"]
        hover = "#e11d48"
    else:  # stop
        bg = c["stop"]
        hover = "#dc2626"

    return f"""
        QPushButton {{
            background-color: {bg};
            color: {c["text_primary"]};
            border: 2px solid {c["border_strong"]};
            border-radius: 8px;
            font-weight: 900;
            font-size: 16px;
        }}
        QPushButton:hover {{
            background-color: {hover};
            border-color: {c["accent"]};
        }}
        QPushButton:pressed {{
            background-color: #111827;
        }}
    """


def get_slider_stylesheet(orientation: str = "horizontal") -> str:
    """Gruby, booth-friendly slider (pitch, trim, EQ)."""
    c = BOOTH_COLORS
    if orientation == "horizontal":
        return f"""
            QSlider::groove:horizontal {{
                height: 8px;
                background: {c["border"]};
                border-radius: 4px;
            }}
            QSlider::handle:horizontal {{
                background: {c["accent"]};
                border: 2px solid {c["text_primary"]};
                width: 22px;
                height: 22px;
                margin: -8px 0;
                border-radius: 11px;
            }}
            QSlider::handle:horizontal:hover {{
                background: {c["text_primary"]};
                border-color: {c["accent"]};
            }}
        """
    else:
        # vertical EQ
        return f"""
            QSlider::groove:vertical {{
                width: 12px;
                background: {c["border"]};
                border-radius: 6px;
            }}
            QSlider::handle:vertical {{
                background: {c["accent"]};
                border: 2px solid {c["text_primary"]};
                height: 24px;
                width: 24px;
                margin: 0 -6px;
                border-radius: 12px;
            }}
        """


def get_bpm_label_stylesheet() -> str:
    """Ogromny BPM w prawym górnym rogu (30-36px, weight 900)."""
    c = BOOTH_COLORS
    return f"""
        QLabel {{
            color: {c["accent"]};
            font-size: 32px;
            font-weight: 900;
            letter-spacing: -0.6px;
            font-family: "Consolas", "JetBrains Mono", monospace;
        }}
    """


def get_section_label_stylesheet() -> str:
    """Etykieta sekcji (HOT CUES, EQ, PITCH...) – uppercase, spaced."""
    c = BOOTH_COLORS
    return f"""
        QLabel {{
            color: {c["text_muted"]};
            font-size: 10px;
            font-weight: 800;
            letter-spacing: 1.8px;
            text-transform: uppercase;
        }}
    """


def get_time_label_stylesheet() -> str:
    """Czas pozycji / duration – czytelny monospace."""
    c = BOOTH_COLORS
    return f"""
        QLabel {{
            color: {c["text_secondary"]};
            font-size: 16px;
            font-weight: 700;
            font-family: "Consolas", "JetBrains Mono", monospace;
        }}
    """


def get_value_label_stylesheet() -> str:
    """Etykieta wartości (np. pitch 12.3%, suwaki) – czytelna, monospace."""
    c = BOOTH_COLORS
    return f"""
        QLabel {{
            color: {c["text_primary"]};
            font-weight: 700;
            font-size: 13px;
            font-family: "Consolas", "JetBrains Mono", monospace;
        }}
    """


def apply_booth_palette_to_widget(widget: Any) -> None:
    """
    Szybka aplikacja globalnego tła booth na widget (dla kontenerów).
    Używać oszczędnie – lepiej konkretne get_*_stylesheet.
    """
    c = BOOTH_COLORS
    widget.setStyleSheet(f"""
        QWidget {{
            background-color: {c["bg"]};
            color: {c["text_primary"]};
        }}
    """)


# Przydatne stałe rozmiarów (booth-friendly)
BOOTH_SIZES = {
    "hotcue_pad": (82, 62),           # zawsze 2x4 grid
    "hotcue_pad_small": (76, 56),
    "waveform_min_height_single": 260,
    "waveform_min_height_console": 200,
    "transport_play": (96, 58),
    "transport_cue": (78, 52),
    "transport_stop": (68, 52),
    "pitch_slider_width": 180,
    "eq_slider_height": 100,
    "crossfader_height": 34,
    # Compact / pilot-like sizes (per SZPIEG spec for single odt)
    "compact_transport_play": (52, 32),
    "compact_transport_cue": (42, 28),
    "compact_transport_stop": (36, 28),
    "compact_waveform_min_height": 80,
    "compact_bpm_font": 14,
    "compact_title_font": 11,
    "compact_time_font": 10,
    "compact_status_font": 9,
}

def get_button_stylesheet(variant: str = "default") -> str:
    """Spójne style dla przycisków transportowych i toggle (KEY, SYNC, PFL itp.)."""
    c = BOOTH_COLORS
    if variant == "toggle":
        return f"""
            QPushButton {{
                background-color: {c["surface"]};
                color: {c["text_primary"]};
                border: 2px solid {c["border_strong"]};
                border-radius: 6px;
                font-weight: 800;
                font-size: 13px;
            }}
            QPushButton:hover {{
                border-color: {c["accent"]};
            }}
            QPushButton:checked {{
                background-color: {c["accent"]};
                color: {c["bg"]};
                border-color: {c["accent"]};
                font-weight: 900;
            }}
        """
    return f"""
        QPushButton {{
            background-color: {c["surface"]};
            color: {c["text_primary"]};
            border: 2px solid {c["border_strong"]};
            border-radius: 8px;
            font-weight: 800;
            font-size: 15px;
        }}
        QPushButton:hover {{
            border-color: {c["accent"]};
            background-color: #1f2937;
        }}
        QPushButton:pressed {{
            background-color: #111827;
        }}
    """


__all__ = [
    "BOOTH_COLORS", "BOOTH_SIZES",
    "get_deck_panel_stylesheet", "get_hotcue_pad_stylesheet",
    "get_transport_button_stylesheet", "get_slider_stylesheet",
    "get_bpm_label_stylesheet", "get_section_label_stylesheet",
    "get_time_label_stylesheet", "get_value_label_stylesheet",
    "get_button_stylesheet", "apply_booth_palette_to_widget",
]
