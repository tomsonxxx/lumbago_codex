"""
ui/dj/styles.py

Centralna paleta kolorów i helpery stylesheetów w stylu booth (Rekordbox/Traktor).
Zaprojektowane dla słabego oświetlenia klubu, rękawiczek i szybkiej pracy.

Wszystkie stałe i funkcje wyłącznie po polsku w komentarzach/docstringach.
Używaj tych helperów – ZERO inline stylesheetów w nowych widokach!

ZASADY SKALOWANIA (BoothMetrics) — obowiązkowe dla Odtwarzacz + nowych widoków DJ
---------------------------------------------------------------------------------
1. Punkt odniesienia: 96 DPI, panel single = 800 px (normal, 1080p) / 400 px (compact).
2. BoothMetrics.from_environment(logical_dpi, widget_width, screen_width) — auto DPI + profil:
   1080p (1920) → 1.00× | 1440p (2560) → 1.08× | 4K (3840+) → 1.15×
3. Współczynnik końcowy: blend(dpi/96, widget_width/ref_width) clamp [0.82 .. 1.55].
4. Fonty: BoothMetrics.font_px(role); BPM/czas = monospace (Consolas/JetBrains Mono).
5. Transport: min 44 px wysokości po skali; proporcje PLAY:CUE:STOP = 1.0:0.82:0.72.
6. Waveform: min 36% panelu (normal) / 28% (compact); stretch=7.
7. resizeEvent: odśwież metrics gdy scale zmieni się >4%; przeładuj layout + waveform min.
8. compact toggle: from_environment(compact=True/False) + _apply_compact_ui().
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
    # Rekordbox 7 RGB waveform (CDJ-style: czerwień bas / zieleń środek / błękit góra)
    "wave_bg": "#030408",
    "wave_center": "#0e1218",
    "wave_low": "#ff3b3b",       # bas — czerwień (RB RGB)
    "wave_mid": "#3dcc3d",       # środek — zieleń
    "wave_high": "#3d8bff",      # góra — niebieski
    "wave_white": "#f0f2f8",     # szczyty — chłodna biel
    "wave_peak": "#67e8f9",
    "wave_rms": "#1e3a52",
    "wave_cue": "#ff9500",       # marker CUE — bursztyn (RB7)
    "playhead": "#ffffff",       # playhead — biały (RB performance)
    "playhead_glow": "#7ec8ff",
    "sync_active": "#166534",
}

# ------------------------------------------------------------------
# Helpery do generowania stylesheetów (czysta separacja stylów)
# ------------------------------------------------------------------

def get_deck_panel_stylesheet() -> str:
    """Zwraca stylesheet dla głównego panelu decku (surface + border)."""
    c = BOOTH_COLORS
    return f"""
        QFrame#DeckPanel, DeckConsoleView, FocusedDeckView, QFrame#OdtwarzaczPanel, OdtwarzaczView {{
            background-color: {c["surface"]};
            border: 1px solid {c["border"]};
            border-radius: 10px;
        }}
        QFrame#DeckPanel:hover, QFrame#OdtwarzaczPanel:hover {{
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


def get_transport_button_stylesheet(role: str = "play", font_px: int = 16) -> str:
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
            font-size: {font_px}px;
            font-family: "Segoe UI Symbol", "Segoe UI", sans-serif;
            padding: 4px 10px 4px 8px;
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


def get_bpm_label_stylesheet(font_px: int = 32) -> str:
    """Ogromny BPM w prawym górnym rogu (30-36px, weight 900)."""
    c = BOOTH_COLORS
    return f"""
        QLabel {{
            color: {c["accent"]};
            font-size: {font_px}px;
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


def get_time_label_stylesheet(font_px: int = 16) -> str:
    """Czas pozycji / duration – czytelny monospace."""
    c = BOOTH_COLORS
    return f"""
        QLabel {{
            color: {c["text_secondary"]};
            font-size: {font_px}px;
            font-weight: 700;
            font-family: "Consolas", "JetBrains Mono", monospace;
        }}
    """


def get_value_label_stylesheet(font_px: int = 13) -> str:
    """Etykieta wartości (np. pitch 12.3%, suwaki) – czytelna, monospace."""
    c = BOOTH_COLORS
    return f"""
        QLabel {{
            color: {c["text_primary"]};
            font-weight: 700;
            font-size: {font_px}px;
            font-family: "Consolas", "JetBrains Mono", monospace;
        }}
    """


def get_mixer_panel_stylesheet() -> str:
    """Panel miksera (crossfader + master/cue) w Dual Console."""
    c = BOOTH_COLORS
    return (
        f"QFrame#MixerPanel {{ background-color: {c['wave_bg']}; "
        f"border: 1px solid {c['border']}; border-radius: 8px; }}"
    )


def deck_channel_badge_stylesheet(metrics: BoothMetrics) -> str:
    """Etykiety kanału A/B przy crossfaderze."""
    fs = metrics.font_px("bpm")
    return (
        f"color: #00e0ff; font-size: {fs}px; font-weight: 900; "
        f"min-width: {metrics.px(18)}px; letter-spacing: 1px;"
    )


def action_button_stylesheet(
    metrics: BoothMetrics,
    *,
    active: bool = False,
    role: str = "default",
) -> str:
    """Kompaktowe przyciski MEM / LOOP / IN / OUT ze skalowaniem."""
    c = BOOTH_COLORS
    fs = max(9, metrics.font_px("transport") - 1)
    sizes = {
        "mem": (32, 26),
        "loop_in": (40, 26),
        "loop_out": (44, 26),
        "loop": (52, 26),
        "default": (36, 26),
    }
    raw_w, raw_h = sizes.get(role, sizes["default"])
    w, h = metrics.px(raw_w), metrics.px(raw_h)
    if role == "loop" and active:
        bg, fg, border = c["loop"], c["text_primary"], c["accent"]
    elif active:
        bg = c.get("sync_active", "#166534")
        fg, border = "#e0f2e0", bg
    else:
        bg, fg, border = c["surface"], c["text_primary"], c["border_strong"]
    return (
        f"QPushButton {{ background-color: {bg}; color: {fg}; border: 2px solid {border}; "
        f"border-radius: 6px; font-weight: 800; font-size: {fs}px; min-width: {w}px; "
        f"max-width: {w}px; min-height: {h}px; max-height: {h}px; }}"
        f"QPushButton:hover {{ border-color: {c['accent']}; }}"
        f"QPushButton:checked {{ background-color: {c['loop']}; color: {c['text_primary']}; "
        f"border-color: {c['accent']}; }}"
    )


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


# Profile rozdzielczości — boost czytelności na większych monitorach (Windows DPI)
BOOTH_RESOLUTION_PROFILES: dict[str, dict[str, float | int]] = {
    "1080p": {"min_screen_w": 0, "scale_boost": 1.0},
    "1440p": {"min_screen_w": 2200, "scale_boost": 1.08},
    "4k": {"min_screen_w": 3440, "scale_boost": 1.15},
}

# Tokeny projektu @ 96 DPI, panel ~800 px (1080p) — źródło prawdy dla BoothMetrics
BOOTH_TOKENS: dict[str, dict[str, int | float | tuple[int, int]]] = {
    "normal": {
        "ref_width": 800,
        "margin_h": 24,
        "margin_v": 20,
        "spacing": 14,
        "title_font": 16,
        "bpm_font": 28,
        "time_font": 14,
        "status_font": 10,
        "transport_font": 14,
        "transport_play": (88, 50),
        "transport_cue": (72, 46),
        "transport_stop": (64, 46),
        # per SZPIEG research 2026-07-14 plan rozbudowy Faza1 Polish (compact highDPI/extreme) + Analyzer + Plan "nowa lista" + CHECKLIST (waveform ≥220px single): synced to BOOTH_SIZES/expected mins; dynamic px() + from_environment clamp nadal nadrabia dla highDPI/4k. Must document identical.
        "wave_min_h": 220,
        "wave_stretch": 7,
        "spin_size": 20,
        "bpm_min_w": 92,
        "transport_gap": 12,
    },
    "deck_focused": {
        "ref_width": 800,
        "margin_h": 24,
        "margin_v": 20,
        "spacing": 18,
        "title_font": 17,
        "bpm_font": 30,
        "time_font": 15,
        "status_font": 10,
        "transport_font": 14,
        "transport_play": (88, 50),
        "transport_cue": (72, 46),
        "transport_stop": (64, 46),
        "wave_min_h": 200,
        "wave_stretch": 7,
        "spin_size": 20,
        "bpm_min_w": 100,
        "transport_gap": 12,
        "hotcue_pad": (80, 58),
    },
    "deck_console": {
        "ref_width": 520,
        "margin_h": 14,
        "margin_v": 12,
        "spacing": 12,
        "title_font": 14,
        "bpm_font": 24,
        "time_font": 13,
        "status_font": 9,
        "transport_font": 12,
        "transport_play": (72, 44),
        "transport_cue": (60, 40),
        "transport_stop": (54, 40),
        "wave_min_h": 148,
        "wave_stretch": 5,
        "spin_size": 18,
        "bpm_min_w": 80,
        "transport_gap": 10,
        "hotcue_pad": (58, 44),
        "pro_btn": (50, 28),
    },
    "dual_mixer": {
        "ref_width": 1100,
        "margin_h": 12,
        "margin_v": 10,
        "spacing": 10,
        "title_font": 11,
        "bpm_font": 16,
        "time_font": 12,
        "status_font": 9,
        "transport_font": 11,
        "transport_play": (64, 40),
        "transport_cue": (54, 38),
        "transport_stop": (48, 38),
        "wave_min_h": 0,
        "wave_stretch": 0,
        "spin_size": 16,
        "bpm_min_w": 0,
        "transport_gap": 8,
        "crossfader_h": 22,
        "crossfader_max_w": 240,
        "mixer_slider_w": 100,
        "mixer_slider_w_cue": 88,
        "pro_btn": (54, 30),
        "deck_badge_font": 16,
    },
    "compact": {
        "ref_width": 400,
        # per SZPIEG research 2026-06-25 DJ checklist + Plan + clean Windows Szpieg + Mixxx/Winamp tight:
        # reduce empty bottom, tight margins/spacing/spin for extreme compact + highDPI pilot (Winamp-mini feel, booth multi-mon).
        # minimal air zachowany ale pack bottom ~2px effective; spin mniejszy dla skalowalności.
        # per SZPIEG research 2026-07-14 plan rozbudowy Faza1 Polish (highDPI/extreme + verifs) + Analyzer refined: wave_min_h synced to >=80 + BOOTH_SIZES compact_waveform_min_height; px() + clamp ensure no cut in 280x200 extreme. Must document identical.
        "margin_h": 6,
        "margin_v": 4,
        "spacing": 4,
        "title_font": 11,
        "bpm_font": 13,
        "time_font": 10,
        "status_font": 9,
        "transport_font": 10,
        "transport_play": (48, 32),
        "transport_cue": (40, 30),
        "transport_stop": (34, 30),
        # per SZPIEG research 2026-07-14 plan rozbudowy Faza1 Polish (compact highDPI/extreme + verifs) + Analyzer refined lista: wave_min_h synced to 80 to match CHECKLIST/BOOTH_SIZES compact_waveform_min_height >=80; px() + from_environment clamp + highDPI scale ensure dominant wave no-cut in extreme 280x200 + multi-monitor. Must document identical.
        "wave_min_h": 80,
        "wave_stretch": 7,
        "spin_size": 14,
        "bpm_min_w": 60,
        "transport_gap": 6,
    },
}


# Ikony booth — Unicode @ Segoe UI Symbol (Windows); tekst fallback dla czytelności
BOOTH_ICONS: dict[str, dict[str, str]] = {
    "play": {"symbol": "▶", "label": "ODTWÓRZ", "playing": "❚❚  PAUZA"},
    "cue": {"symbol": "", "label": "CUE"},
    "stop": {"symbol": "■", "label": "STOP"},
    "sync": {"symbol": "⟳", "label": "SYNC", "active": "SYNC ✓"},
    "loop": {"symbol": "↻", "label": "LOOP"},
    "quantize": {"symbol": "", "label": "Q"},
    "pfl": {"symbol": "HP", "label": "PFL"},
    "memory_save": {"symbol": "", "label": "S"},
    "memory_recall": {"symbol": "", "label": "R"},
    "deck_a": {"symbol": "", "label": "A"},
    "deck_b": {"symbol": "", "label": "B"},
}


def booth_transport_label(role: str, *, playing: bool = False) -> str:
    """Tekst transportu bez symbolu Unicode (para z ikoną SVG)."""
    info = BOOTH_ICONS.get(role, {})
    if role == "play":
        if playing:
            return str(info.get("playing", "PAUZA")).split()[-1]
        return str(info.get("label", "ODTWÓRZ"))
    return str(info.get("label", role.upper()))


def booth_transport_text(role: str, *, playing: bool = False, compact: bool = False) -> str:
    """Etykieta przycisku transportu (CDJ: CUE | PLAY | STOP)."""
    info = BOOTH_ICONS.get(role, {})
    if role == "play":
        if playing:
            return "❚❚" if compact else info.get("playing", "❚❚  PAUZA")
        sym = info.get("symbol", "▶")
        if compact:
            return sym
        lbl = info.get("label", "ODTWÓRZ")
        return f"{sym}  {lbl}".strip() if sym else lbl
    if compact and role == "stop":
        return info.get("symbol", "■") or "■"
    if compact and role == "cue":
        return info.get("label", "CUE")
    sym = info.get("symbol", "")
    lbl = info.get("label", role.upper())
    return f"{sym}  {lbl}".strip() if sym else lbl


def booth_toggle_text(role: str, *, active: bool = False) -> str:
    info = BOOTH_ICONS.get(role, {})
    if active and "active" in info:
        return str(info["active"])
    sym = info.get("symbol", "")
    lbl = info.get("label", role.upper())
    return f"{sym} {lbl}".strip() if sym else lbl


def pro_button_stylesheet(metrics: BoothMetrics, *, active: bool = False) -> str:
    """Kompaktowy przycisk pro (SYNC/PFL/Q) ze skalowaniem."""
    c = BOOTH_COLORS
    w, h = metrics.pro_button_size()
    fs = max(9, metrics.font_px("transport") - 1)
    if active:
        bg = c.get("sync_active", "#166534")
        fg = "#e0f2e0"
        border = bg
    else:
        bg = c["surface"]
        fg = c["text_primary"]
        border = c["border_strong"]
    return (
        f"QPushButton {{ background-color: {bg}; color: {fg}; border: 2px solid {border}; "
        f"border-radius: 6px; font-weight: 800; font-size: {fs}px; min-width: {w}px; "
        f"max-width: {w}px; min-height: {h}px; max-height: {h}px; }}"
        f"QPushButton:hover {{ border-color: {c['accent']}; }}"
        f"QPushButton:checked {{ background-color: {c['accent']}; color: {c['bg']}; "
        f"border-color: {c['accent']}; }}"
    )


def _resolution_scale_boost(screen_width: int) -> float:
    if screen_width >= int(BOOTH_RESOLUTION_PROFILES["4k"]["min_screen_w"]):
        return float(BOOTH_RESOLUTION_PROFILES["4k"]["scale_boost"])
    if screen_width >= int(BOOTH_RESOLUTION_PROFILES["1440p"]["min_screen_w"]):
        return float(BOOTH_RESOLUTION_PROFILES["1440p"]["scale_boost"])
    return float(BOOTH_RESOLUTION_PROFILES["1080p"]["scale_boost"])


class BoothMetrics:
    """Skalowanie UI booth — tryb normal/compact + DPI + szerokość panelu + profil ekranu."""

    _MONO = '"Consolas", "JetBrains Mono", monospace'

    def __init__(
        self,
        compact: bool = False,
        mode: str = "normal",
        dpi_scale: float = 1.0,
        width_scale: float = 1.0,
        resolution_boost: float = 1.0,
    ) -> None:
        self.compact = compact
        self.mode = "compact" if compact else mode
        self._tokens = BOOTH_TOKENS.get(self.mode, BOOTH_TOKENS["normal"])
        self._dpi_scale = float(dpi_scale)
        self._width_scale = float(width_scale)
        self._resolution_boost = float(resolution_boost)
        blended = max(self._dpi_scale * self._resolution_boost, self._width_scale * 0.92)
        self._scale = min(1.55, max(0.82, blended))

    @classmethod
    def from_environment(
        cls,
        *,
        compact: bool = False,
        mode: str = "normal",
        logical_dpi: float = 96.0,
        widget_width: int = 0,
        screen_width: int = 1920,
    ) -> BoothMetrics:
        """
        Auto-skalowanie pod Windows DPI + szerokość panelu + profil 1080p/1440p/4K.
        mode: normal | compact | deck_focused | deck_console
        """
        token_key = "compact" if compact else mode
        tokens = BOOTH_TOKENS.get(token_key, BOOTH_TOKENS["normal"])
        ref_w = max(1, int(tokens["ref_width"]))  # type: ignore[arg-type]
        dpi_scale = min(1.6, max(0.88, float(logical_dpi) / 96.0))
        if widget_width > 120:
            width_scale = min(1.4, max(0.85, widget_width / ref_w))
        else:
            width_scale = 1.0
        res_boost = _resolution_scale_boost(int(screen_width))
        return cls(
            compact=compact,
            mode=token_key,
            dpi_scale=dpi_scale,
            width_scale=width_scale,
            resolution_boost=res_boost,
        )

    def hotcue_pad_size(self) -> tuple[int, int]:
        raw = self._tokens.get("hotcue_pad", (80, 58))
        w, h = raw  # type: ignore[misc]
        return self.px(w), self.px(h)

    @property
    def scale_factor(self) -> float:
        return self._scale

    def px(self, value: int | float) -> int:
        return max(1, int(round(float(value) * self._scale)))

    def font_px(self, role: str) -> int:
        key = f"{role}_font"
        raw = self._tokens.get(key, 12)
        return self.px(int(raw))  # type: ignore[arg-type]

    def size(self, role: str) -> tuple[int, int]:
        raw = self._tokens.get(role, (64, 40))
        w, h = raw  # type: ignore[misc]
        return self.px(w), self.px(h)

    def layout_margins(self) -> tuple[int, int, int, int]:
        h = self.px(int(self._tokens["margin_h"]))  # type: ignore[arg-type]
        v = self.px(int(self._tokens["margin_v"]))  # type: ignore[arg-type]
        # per SZPIEG research 2026-06-25 DJ checklist + Plan + Mixxx/Winamp tight: reduce empty bottom further
        # for extreme compact/highDPI (pilot tight pack, avoid push empty space in Winamp-like floating).
        bottom = max(1, v // 2) if self.compact else v   # was max(2, v//3)
        return h, v, h, bottom

    def layout_spacing(self) -> int:
        return self.px(int(self._tokens["spacing"]))  # type: ignore[arg-type]

    def wave_min_height(self) -> int:
        return self.px(int(self._tokens["wave_min_h"]))  # type: ignore[arg-type]

    def wave_stretch(self) -> int:
        return int(self._tokens["wave_stretch"])  # type: ignore[arg-type]

    def title_stylesheet(self) -> str:
        c = BOOTH_COLORS
        return (
            f"font-size: {self.font_px('title')}px; font-weight: 700; "
            f"color: {c['text_primary']};"
        )

    def bpm_stylesheet(self) -> str:
        return get_bpm_label_stylesheet(self.font_px("bpm"))

    def time_stylesheet(self) -> str:
        return get_time_label_stylesheet(self.font_px("time"))

    def status_stylesheet(self) -> str:
        c = BOOTH_COLORS
        return (
            f"color: {c.get('text_muted', '#6b7688')}; "
            f"font-size: {self.font_px('status')}px; font-weight: 600;"
        )

    def section_label_stylesheet(self) -> str:
        c = BOOTH_COLORS
        fs = max(8, self.font_px("status"))
        return (
            f"color: {c['text_muted']}; font-size: {fs}px; font-weight: 800; "
            f"letter-spacing: 1.6px;"
        )

    def value_label_stylesheet(self) -> str:
        return get_value_label_stylesheet(max(10, self.font_px("time") - 1))

    def transport_stylesheet(self, role: str) -> str:
        return get_transport_button_stylesheet(role, self.font_px("transport"))

    def bpm_min_width(self) -> int:
        return self.px(int(self._tokens["bpm_min_w"]))  # type: ignore[arg-type]

    def spin_size(self) -> int:
        return self.px(int(self._tokens["spin_size"]))  # type: ignore[arg-type]

    def transport_gap(self) -> int:
        return self.px(int(self._tokens.get("transport_gap", 12)))  # type: ignore[arg-type]

    def min_transport_height(self) -> int:
        """Minimalna wysokość przycisku transportu po skali (touch target 44 px @ 1.0)."""
        return max(self.px(44), self.size("transport_stop")[1])

    def crossfader_height(self) -> int:
        raw = self._tokens.get("crossfader_h", 22)
        return self.px(int(raw))  # type: ignore[arg-type]

    def crossfader_max_width(self) -> int:
        raw = self._tokens.get("crossfader_max_w", 240)
        return self.px(int(raw))  # type: ignore[arg-type]

    def mixer_slider_width(self, *, cue: bool = False) -> int:
        key = "mixer_slider_w_cue" if cue else "mixer_slider_w"
        raw = self._tokens.get(key, 140 if cue else 160)
        return self.px(int(raw))  # type: ignore[arg-type]

    def pro_button_size(self) -> tuple[int, int]:
        raw = self._tokens.get("pro_btn", (54, 30))
        w, h = raw  # type: ignore[misc]
        return self.px(w), self.px(h)

    def eq_slider_height(self) -> int:
        return self.px(100)

    def pitch_slider_width(self) -> int:
        return self.px(170 if self.mode == "deck_focused" else 150)


# Przydatne stałe rozmiarów (booth-friendly) — legacy; preferuj BoothMetrics
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
    # Compact pilot window shrink/floating per SZPIEG/Plan/FIXER polish (pilot-like always-on-top option, min for multi-mon booth)
    "compact_window_min": (420, 300),
    "compact_window_floating_hint": True,  # used for setWindowFlags StaysOnTop in toggle
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
    "BOOTH_COLORS",
    "BOOTH_ICONS",
    "BOOTH_SIZES",
    "BOOTH_TOKENS",
    "BOOTH_RESOLUTION_PROFILES",
    "BoothMetrics",
    "booth_transport_text",
    "booth_transport_label",
    "booth_toggle_text",
    "pro_button_stylesheet",
    "get_mixer_panel_stylesheet",
    "deck_channel_badge_stylesheet",
    "action_button_stylesheet",
    "get_deck_panel_stylesheet",
    "get_hotcue_pad_stylesheet",
    "get_transport_button_stylesheet",
    "get_slider_stylesheet",
    "get_bpm_label_stylesheet",
    "get_section_label_stylesheet",
    "get_time_label_stylesheet",
    "get_value_label_stylesheet",
    "get_button_stylesheet",
    "apply_booth_palette_to_widget",
]
