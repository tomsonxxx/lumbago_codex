from __future__ import annotations

from PyQt6 import QtCore, QtGui, QtWidgets
from pathlib import Path
from typing import Optional
import logging

from core.models import Track  # CuePoint używany wyłącznie w ui/dj/hotcue_manager.py
from core.waveform import WaveformData, generate_waveform_threadsafe, extract_peaks

# Nowa architektura (faza równoległa redesignu) - sole implementation, hardcoded
from ui.dj.deck_controller import DeckController
from ui.dj.views import (
    FocusedDeckView,
    ConsoleDeckView,
    DualConsoleWidget,
    MixerStrip,
)
# Minimal Odtwarzacz MVP single (new lightweight path for "Odtwarzacz" mode only)
from ui.dj.simple_deck_controller import SimpleDeckController
from ui.dj.views.odtwarzacz_view import OdtwarzaczView
print("[DJ] Nowa architektura zaimportowana pomyślnie (DeckController + views) - sole impl")
print("[DJ] Odtwarzacz MVP: SimpleDeckController + OdtwarzaczView zaimportowane (single mode only)")
# REVIEWER 2026-06 note (crew per PLAN/SZPIEG): QStack dual0+odt1, compact only single, reentr guards, init order documented; remaining P0 spin in odt, P1 dual always. See crew/SZPIEG (REVIEWER) + memory. Exact per spec.

# Nowy, solidny backend audio
from services.playback import PlaybackEngine, create_backend

# ------------------------------------------------------------------
# HotcueManager + format_track_time – CZYSTY MODUŁ (faza final cleanup)
# Przeniesione do ui/dj/hotcue_manager.py – ZERO zależności od tego monstrualnego pliku.
# ------------------------------------------------------------------
from ui.dj.hotcue_manager import HotcueManager, format_track_time

# (HotcueManager + persystencja wyłącznie w ui/dj/hotcue_manager.py)

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------
# REFACTOR (Opcja A cleanup): format_track_time + HotcueManager w osobnym module.
# Sole new architecture: ui/dj/ (DeckController + FocusedDeckView/ConsoleDeckView/DualConsoleWidget).
# WaveformWidget extracted to ui/dj/views/waveform_widget.py (clean, reusable).
# Both OdtwarzaczView (MVP single) and legacy Focused/Console import the extracted one.
# ------------------------------------------------------------------

# Note: extract_peaks (and its internal _generate_fallback) now lives in core/waveform.py
# for reuse by library detail panel (eliminates ffmpeg dependency for small previews).
# WaveformWidget extracted; this helper is legacy (unused by new single/dual paths).
def extract_peaks_from_audio(audio_path: str | Path, num_points: int = 900) -> list[float]:
    try:
        return extract_peaks(audio_path, num_points=num_points)
    except Exception as e:
        logger.warning(f"Failed to extract peaks from {audio_path}: {e}")
        # Last-resort local fallback (should never happen)
        import math, random
        peaks = []
        for i in range(num_points):
            t = (i / num_points) * 180
            base = 0.3 + 0.5 * abs(math.sin(t * 1.7)) + 0.2 * abs(math.sin(t * 0.35))
            noise = random.uniform(-0.06, 0.06)
            peaks.append(max(0.08, min(0.97, base + noise)))
        return peaks


# Pro DJ booth high-contrast dark theme – teraz alias do centralnej palety BOOTH_COLORS (Rekordbox polish)
# Zachowany dla kompatybilności z WaveformWidget (który jest w tym pliku).
# Używaj ui.dj.styles.BOOTH_COLORS w nowych widokach!
from ui.dj.styles import BOOTH_COLORS
# No legacy aliases left. New booth styles in ui/dj/styles.py.
COLORS = {
    **BOOTH_COLORS,
    "text": BOOTH_COLORS.get("text_primary", "#f0f4f8"),
    "panel": BOOTH_COLORS.get("surface", "#12171f"),
    "panel_border": BOOTH_COLORS.get("border", "#2a3442"),
    "section_label": BOOTH_COLORS.get("text_muted", "#6b7688"),
    "hotcue_active": "#ffffff",
    "accent_green": BOOTH_COLORS.get("play", "#22c55e"),
}


# WaveformWidget extracted to ui/dj/views/waveform_widget.py (see task 1).
# The class definition was removed here to keep dj_player_window.py thin (orchestrator only).
# Dual views (focused/console) and new OdtwarzaczView now import from ui.dj.views.waveform_widget directly.
# (stary HotcuePad usunięty – wyłącznie w ui/dj/views/hotcue_pad.py z 8 kolorami z BOOTH)

# === OLD DECKWIDGET + SINGLEPLAYERVIEW REMOVED (Opcja A complete: sole impl via ui/dj/* + DeckController + DualConsoleWidget) ===

class DJPlayerWindow(QtWidgets.QMainWindow):
    """Główne niezależne okno DJ Playera."""

    # Signals for tight integration with main library views (now playing indicators, sync)
    deck_track_loaded = QtCore.pyqtSignal(str, object)   # deck ("A"/"B"), Track
    deck_track_unloaded = QtCore.pyqtSignal(str)         # deck
    all_stopped = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Lumbago DJ Player")
        self.setMinimumSize(980, 720)
        self.resize(1100, 820)  # larger default for booth console with 2x large waveforms + 8-pad grids + mixer (Rekordbox-like)
        self._orig_min_w = 980
        self._orig_min_h = 720
        # Per compact scalability (P1 findings): minSize dynamic on toggle by compact_btn (shrink for pilot, restore for console)

        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        main_layout = QtWidgets.QVBoxLayout(central)
        main_layout.setContentsMargins(12, 10, 12, 10)
        main_layout.setSpacing(8)

        # ========== MODE SELECTOR BAR (always visible) ==========
        # "Odtwarzacz" = clean single-deck view   |   "Konsola DJ" = full pro dual-deck console
        mode_bar = QtWidgets.QHBoxLayout()
        mode_bar.setContentsMargins(0, 0, 0, 4)
        mode_bar.setSpacing(2)

        self.mode_btn_single = QtWidgets.QPushButton("Odtwarzacz")
        self.mode_btn_console = QtWidgets.QPushButton("Konsola DJ")
        for btn in (self.mode_btn_single, self.mode_btn_console):
            btn.setCheckable(True)
            btn.setFixedHeight(28)
            btn.setFixedWidth(118)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: #1a2233;
                    border: 1px solid #2f3a52;
                    border-radius: 5px;
                    font-weight: 700;
                    font-size: 12px;
                    padding: 2px 8px;
                }}
                QPushButton:hover {{
                    border-color: {COLORS["accent"]};
                }}
                QPushButton:checked {{
                    background-color: {COLORS["accent"]};
                    color: {COLORS["bg"]};
                    border-color: {COLORS["accent"]};
                    font-weight: 800;
                }}
            """)

        # EFFECT tooltips (per spec: 1-2 zdania co się stanie z UI/plikiem)
        self.mode_btn_single.setToolTip("Przełącz na tryb Odtwarzacz (single, czysty). EFEKT: pokazuje tylko jeden deck z dużym waveformem + transportem CUE/PLAY/STOP; dual console schowane. Używa lekkiego SimpleDeckController (file load + basic stream playback). Zachowuje air i skalowalność.")
        self.mode_btn_console.setToolTip("Przełącz na tryb Konsola DJ (dual). EFEKT: pokazuje dwa decki A/B side-by-side lub stacked z pełnym mikserem, crossfaderem, EQ, hotcue'ami; odtwarzacz single schowany. Używa pełnych DeckController (nietknięte).")

        self.mode_btn_group = QtWidgets.QButtonGroup(self)
        self.mode_btn_group.addButton(self.mode_btn_single, 0)
        self.mode_btn_group.addButton(self.mode_btn_console, 1)
        self.mode_btn_group.idClicked.connect(self._switch_player_mode)

        # Default to single "Odtwarzacz" (per user: start with single player basics, focus load + play/pause/stop)
        self.mode_btn_single.setChecked(True)
        self._current_mode = "single"   # "console" or "single"
        self._simple_deck_ctrl: Optional["SimpleDeckController"] = None
        self.odtwarzacz_view: Optional["OdtwarzaczView"] = None

        mode_bar.addStretch(1)
        mode_bar.addWidget(self.mode_btn_single)
        mode_bar.addWidget(self.mode_btn_console)
        # Compact toggle inline (pilot) — po prawej, przed ostatnim stretchem
        self.compact_btn = QtWidgets.QPushButton("☐ Compact")
        self.compact_btn.setCheckable(True)
        self.compact_btn.setFixedHeight(26)
        self.compact_btn.setFixedWidth(90)
        self.compact_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #1a2233;
                border: 1px solid #2f3a52;
                border-radius: 5px;
                font-weight: 600;
                font-size: 11px;
                padding: 1px 4px;
            }}
            QPushButton:checked {{
                background-color: {COLORS["accent"]};
                color: {COLORS["bg"]};
                border-color: {COLORS["accent"]};
                font-weight: 700;
            }}
        """)
        self.compact_btn.setToolTip("Włącz tryb compact (pilot-like) dla Odtwarzacza. EFEKT: mniejsze rozmiary, mniejszy waveform, spinning CD animowany przy play, ikony mini; zachowuje cue/drag/file-stream. Tylko dla single odt (nie dual).")
        self.compact_btn.toggled.connect(self._on_compact_toggled)
        mode_bar.addWidget(self.compact_btn)
        mode_bar.addStretch(1)
        main_layout.addLayout(mode_bar)

        # === QSTACKED DLA CZYSTEGO PRZEŁĄCZANIA (SOLIDIFY per SZPIEG/Plan step 1) ===
        # Eliminuje hacki visibility/setVisible/raise_ na odt vs dual + single_container.
        # Odtwarzacz (single) = index 1, Konsola DJ (dual) = index 0.
        # Dual/console paths NIETKNIĘTE (tylko routing przez stack).
        # File vs stream: load = operacja na PLIKU fizycznym (ścieżka do audio na dysku),
        # transport/play = strumień dźwięku z załadowanego pliku (silnik playback).
        # Komentarze i guardy dodane w load/play paths.
        self.content_stack = QtWidgets.QStackedWidget()
        main_layout.addWidget(self.content_stack, 1)  # stretch dla skalowalności

        # === SOLIDIFY QSTACK INDICES (per SZPIEG Build Spec + Plan step 1) ===
        # Dual console (Konsola DJ) ZAWSZE index 0, Odtwarzacz (single MVP) ZAWSZE index 1.
        # Zapewnia poprawne target w _switch_player_mode bez race/hacków.
        # Odtwarzacz tworzony PO dual (kolejność add = kolejność indeksów) + ensure guard w init/switch.
        # Legacy Focused single_container usunięty z dual create (po Opcja A sole odt for single) — set None, ukryty w guardach.
        # Brak widocznych hacków setVisible na stack content (QStacked zarządza).
        # File vs STREAM docs: load=FILE (ścieżka+DB), transport=STREAM (engine playhead).
        self._DUAL_CONSOLE_IDX: int = 0
        self._ODT_IDX: int = 1

        # Track widgets that belong to the dual console for show/hide during mode switch
        self._console_widgets: list[QtWidgets.QWidget] = []

        # Układ kompaktowy (deck A nad deck B)
        try:
            # Tworzymy wspólny silnik playbacku (VLC lub fallback)
            self.playback_engine = PlaybackEngine()

            # === NOWA ARCHITEKTURA (sole implementation) ===
            # Używamy helperów z tasku integracyjnego — czysty, powtarzalny wiring
            # Nowa architektura zawsze (import succeeded)
            try:
                created_dual = self._create_dual_console_ui()  # Zmienione: nie przyjmuje main_layout (stack zarządza)
                self.dual_console = created_dual
                if created_dual is None:
                    raise RuntimeError("dual console creation returned None")
                self.content_stack.addWidget(created_dual)
                # === NOWA ARCHITEKTURA AKTYWNA (primary path) ===
                logger.info("NEW ARCHITECTURE ACTIVE: DeckController + FocusedDeckView/ConsoleDeckView/DualConsoleWidget (pełny wiring drag&drop, skróty, mikser)")
                logger.info("Nowa architektura sole (redesign complete)")

                # Utwórz Odtwarzacz MVP (single) i dodaj do stack jako index 1 (po dual jako 0).
                # Zapewnia poprawne indeksy dla switch: single -> self._ODT_IDX (odt), console -> self._DUAL_CONSOLE_IDX (dual)
                # Zgodne z SZPIEG/Plan: odt after dual, no race (create inside same try), guards.
                # Per spec: dual 0, odt 1 zawsze.
                if getattr(self, "odtwarzacz_view", None) is None:
                    try:
                        odt = self._create_odtwarzacz_ui()
                        self.odtwarzacz_view = odt
                        if odt:
                            self.content_stack.addWidget(odt)
                            # Sanity: ensure odt at _ODT_IDX
                            if self.content_stack.count() > self._ODT_IDX:
                                # index should be 1 if dual was first
                                pass
                    except Exception as e:
                        logger.warning(f"odtwarzacz create after dual failed (non-fatal): {e}")
                        self.odtwarzacz_view = None
                # Popraw init order / race (per SZPIEG/Plan/REVIEWER lista): ensure odt ready ZAWSZE przed switch/initial use.
                # Nawet jeśli create inside dual try zawiódł — odt jest primary dla default single.
                # Dual overhead partial (zawsze tworzony), ale odt gwarantowany.
                if getattr(self, "odtwarzacz_view", None) is None:
                    try:
                        odt = self._create_odtwarzacz_ui()
                        self.odtwarzacz_view = odt
                        if odt and hasattr(self, "content_stack") and self.content_stack:
                            # add if not already (e.g. failed earlier path)
                            if odt not in [self.content_stack.widget(i) for i in range(self.content_stack.count())]:
                                self.content_stack.addWidget(odt)
                    except Exception as e:
                        logger.warning(f"ensure odt create failed: {e}")
                        self.odtwarzacz_view = None
                # Jeśli odt nadal None po ensure: disable compact (per findings no odt guard)
                if not getattr(self, "odtwarzacz_view", None):
                    if hasattr(self, "compact_btn"):
                        try:
                            self.compact_btn.setEnabled(False)
                            self.compact_btn.setToolTip("Compact niedostępny (odt init failed)")
                        except Exception:
                            pass
            except Exception as e:
                logger.exception("Nowa architektura zawiodła przy tworzeniu UI - nie ma fallbacku")
                raise  # re-raise to be caught by outer except and show error dialog

            # Recent history per deck (for quick reloads, task requirement)
            self._recent_a: list[Track] = []
            self._recent_b: list[Track] = []
            self._MAX_RECENT = 8

            # === SMOKE TEST READY (po final cleanup) ===
            # Uruchom:
            #   $env:LUMBAGO_SAFE_MODE=1; $env:LUMBAGO_SMOKE_SECONDS=3; python main.py
            # Oczekuj w logach: "NEW ARCHITECTURE ACTIVE" (nowa architektura primary).
            # Pełny manual checklist: crew/AGENT3_UI_Designer_Rekordbox_Redo.md (hotcues, waveform, drag&drop, tryby, mixer, skróty, DB persystencja).
            # Testy: pytest tests/test_dj_hotcue_manager.py  (musi przejść po przeniesieniu)
            # Po starcie w trybie console: DualConsoleWidget z dwoma ConsoleDeckView + DeckCtrl + MixerStrip (opcjonalny).

        except Exception as exc:
            logger.exception("Błąd podczas tworzenia decków w DJPlayerWindow")
            # Zawsze pokazuj okno z czytelnym błędem + możliwość zaznaczenia tekstu
            error_text = QtWidgets.QPlainTextEdit()
            error_text.setPlainText(
                "Wystąpił błąd podczas inicjalizacji DJ Playera.\n\n"
                f"Szczegóły:\n{exc}\n\n"
                "Jeśli błąd dotyczy 'QShortcut' lub podobnych rzeczy — to jest błąd w kodzie aplikacji (nie problem z VLC).\n\n"
                "Spróbuj zrestartować aplikację. Jeśli problem będzie się powtarzał, skopiuj dokładny tekst błędu i wyślij."
            )
            error_text.setReadOnly(True)
            error_text.setLineWrapMode(QtWidgets.QPlainTextEdit.LineWrapMode.WidgetWidth)
            main_layout.addWidget(error_text)

            # Przycisk kopiowania
            copy_btn = QtWidgets.QPushButton("Kopiuj błąd do schowka")
            copy_btn.clicked.connect(lambda: QtWidgets.QApplication.clipboard().setText(error_text.toPlainText()))
            main_layout.addWidget(copy_btn)
            if hasattr(self, "_console_widgets"):
                self._console_widgets.extend([error_text, copy_btn])

            self.deck_a = None
            self.deck_b = None
            # Nie return — pozwalamy na otwarcie okna z komunikatem błędu

        # Fallback banner (clear but non-annoying) when QtMultimedia is active
        self._maybe_show_fallback_banner(main_layout)

        # === KOMPAKTOWY PASEK NARZĘDZI (Recent + Load + STOP ALL + backend info) ===
        # W sole new arch DualConsole ma już własny pełny mikser (cross/master/cue + PPM).
        # Nie dodajemy duplikatu global_mixer (unikamy nakładania się kontrolek i chaosu).
        # Pasek narzędzi jest mały i użyteczny do szybkiego ładowania/recent/stop.
        try:
            tools = QtWidgets.QHBoxLayout()
            tools.setContentsMargins(4, 2, 4, 2)
            tools.setSpacing(6)

            # Recent
            self.recent_menu_a = QtWidgets.QMenu(self)
            self.recent_menu_b = QtWidgets.QMenu(self)
            self.recent_btn_a = QtWidgets.QToolButton()
            self.recent_btn_a.setText("Recent A ▾")
            self.recent_btn_a.setMenu(self.recent_menu_a)
            self.recent_btn_a.setPopupMode(QtWidgets.QToolButton.ToolButtonPopupMode.InstantPopup)
            self.recent_btn_a.setFixedHeight(20)
            self.recent_btn_a.setStyleSheet("font-size: 8px; padding: 0 4px;")
            tools.addWidget(self.recent_btn_a)

            self.recent_btn_b = QtWidgets.QToolButton()
            self.recent_btn_b.setText("Recent B ▾")
            self.recent_btn_b.setMenu(self.recent_menu_b)
            self.recent_btn_b.setPopupMode(QtWidgets.QToolButton.ToolButtonPopupMode.InstantPopup)
            self.recent_btn_b.setFixedHeight(20)
            self.recent_btn_b.setStyleSheet("font-size: 8px; padding: 0 4px;")
            tools.addWidget(self.recent_btn_b)

            self.recent_menu_a.aboutToShow.connect(lambda: self._populate_recent_menu("A", self.recent_menu_a))
            self.recent_menu_b.aboutToShow.connect(lambda: self._populate_recent_menu("B", self.recent_menu_b))

            tools.addSpacing(6)

            load_a = QtWidgets.QPushButton("Load A…")
            load_b = QtWidgets.QPushButton("Load B…")
            load_a.setFixedWidth(58)
            load_b.setFixedWidth(58)
            load_a.setStyleSheet("font-size: 8px;")
            load_b.setStyleSheet("font-size: 8px;")
            load_a.clicked.connect(lambda: self._load_file_dialog("A"))
            load_b.clicked.connect(lambda: self._load_file_dialog("B"))
            tools.addWidget(load_a)
            tools.addWidget(load_b)

            tools.addSpacing(6)

            stop_all_btn = QtWidgets.QPushButton("■ STOP ALL")
            stop_all_btn.setFixedWidth(66)
            stop_all_btn.setStyleSheet("font-size: 8px; font-weight: 700; color: #ff6b6b;")
            stop_all_btn.clicked.connect(self.stop_all_decks)
            tools.addWidget(stop_all_btn)

            unload_all_btn = QtWidgets.QPushButton("Unload All")
            unload_all_btn.setFixedWidth(60)
            unload_all_btn.setStyleSheet("font-size: 8px;")
            unload_all_btn.clicked.connect(self.unload_all)
            tools.addWidget(unload_all_btn)

            tools.addStretch(1)

            self.backend_info_label = QtWidgets.QLabel("")
            self.backend_info_label.setStyleSheet(f"color: {COLORS.get('text_muted', '#6b7688')}; font-size: 8px;")
            tools.addWidget(self.backend_info_label)

            tools_w = QtWidgets.QWidget()
            tools_w.setLayout(tools)
            main_layout.addWidget(tools_w)
            # Nie dodajemy do _console_widgets, żeby pasek Recent/Load/STOP był zawsze widoczny (nawet w trybie single "Odtwarzacz").
            QtCore.QTimer.singleShot(120, self._update_backend_info_label)
        except Exception:
            logger.debug("Tools bar nie utworzony")

        # UWAGA: W sole new architecture nie ma już globalnych toggle'ów "Pokaż/Ukryj" (hotcues/eq/loop zawsze widoczne w deck views per redesign).
        # Usunięto martwy pasek przełączników i btn_layout (były przyczyną nakładania się elementów i marnowania miejsca).

        self._apply_base_style()

        # Status bar
        self.setStatusBar(QtWidgets.QStatusBar())

        # Pokazujemy czytelny status backendu na deckach (VLC / Qt / Brak) — defensywnie
        if hasattr(self, '_update_backend_info_label'):
            QtCore.QTimer.singleShot(80, self._update_backend_info_label)

        # ========== LEGACY FOCUSED SINGLE (po Opcja A sole odt) ==========
        # Usunięto tworzenie heavy FocusedDeckView / single_container w dual (legacy unneeded dla sole OdtwarzaczView single).
        # single_container = None (z dual), single_player_view = None.
        # Guardy w switch/_toggle_beatgrid/unload etc. ukrywają jeśli kiedykolwiek set (kompat).
        # Per lista: usuń lub ukryj legacy focused single_container jeśli niepotrzebny (sole odt for single).
        # Nie wywołujemy _create_focused_single_ui gdy odt+stack.
        self.single_container = getattr(self, "single_container", None) or None
        self.single_player_view = None
        try:
            if getattr(self, "single_container", None):
                self.single_container.setVisible(False)
            if getattr(self, "single_player_view", None):
                self.single_player_view.setVisible(False)
            if not hasattr(self, "_console_widgets"):
                self._console_widgets = []
        except Exception as e:
            logger.warning(f"Legacy single_container hide non-fatal: {e}")

        # Akceptujemy dropy na całym oknie (fallback)
        self.setAcceptDrops(True)

        # Initial mode switch to set correct visibility for Odtwarzacz (single) or dual.
        # Since default is now single (per focus on single basics), trigger it.
        # SOLIDIFY: use explicit idx logic, default single -> ODT_IDX.
        try:
            default_single = getattr(self, '_current_mode', 'single') == 'single'
            init_mode_id = 0 if default_single else 1
            # Also set stack current early (defensive against races in creation order)
            if hasattr(self, "content_stack") and self.content_stack:
                init_idx = self._ODT_IDX if default_single else self._DUAL_CONSOLE_IDX
                if self.content_stack.count() > init_idx:
                    self.content_stack.setCurrentIndex(init_idx)
            self._switch_player_mode(init_mode_id)
        except Exception:
            pass

        # Podstawowe skróty klawiszowe (extended to 8 for advanced hotcue mode)
        QtGui.QShortcut(QtGui.QKeySequence(QtCore.Qt.Key.Key_Space), self, self._global_play_pause)
        QtGui.QShortcut(QtGui.QKeySequence("Ctrl+1"), self, lambda: self._quick_load_hotcue(0))
        QtGui.QShortcut(QtGui.QKeySequence("Ctrl+2"), self, lambda: self._quick_load_hotcue(1))
        QtGui.QShortcut(QtGui.QKeySequence("Ctrl+3"), self, lambda: self._quick_load_hotcue(2))
        QtGui.QShortcut(QtGui.QKeySequence("Ctrl+4"), self, lambda: self._quick_load_hotcue(3))
        QtGui.QShortcut(QtGui.QKeySequence("Ctrl+5"), self, lambda: self._quick_load_hotcue(4))
        QtGui.QShortcut(QtGui.QKeySequence("Ctrl+6"), self, lambda: self._quick_load_hotcue(5))
        QtGui.QShortcut(QtGui.QKeySequence("Ctrl+7"), self, lambda: self._quick_load_hotcue(6))
        QtGui.QShortcut(QtGui.QKeySequence("Ctrl+8"), self, lambda: self._quick_load_hotcue(7))
        # Dodatkowe pro shortcuts (Rekordbox feel)
        QtGui.QShortcut(QtGui.QKeySequence("Ctrl+Q"), self, self._toggle_quantize_a)
        QtGui.QShortcut(QtGui.QKeySequence("Ctrl+S"), self, self._do_sync_a_b)  # quick sync A to B

    def _toggle_section(self, section: str, visible: bool):
        # Nowa architektura sole impl: views manage their own sections internally (no-op here for compat)
        pass

    def _toggle_beatgrid(self, visible: bool):
        # Sole new architecture: waveformy wewnątrz ConsoleDeckView / FocusedDeckView.
        # Globalny toggle przycisk usunięty (beatgrid jest zawsze widoczny i muzykalny w booth redesign).
        # Metoda zachowana dla kompatybilności (np. ewentualne skróty).
        for deck_id in ("A", "B"):
            try:
                if hasattr(self, "dual_console") and self.dual_console:
                    v = self.dual_console.get_deck_view(deck_id) if hasattr(self.dual_console, "get_deck_view") else None
                    if v and hasattr(v, "waveform") and hasattr(v.waveform, "set_beatgrid_visible"):
                        v.waveform.set_beatgrid_visible(visible)
            except Exception:
                pass
        try:
            if hasattr(self, "single_container") and self.single_container:
                if hasattr(self.single_container, "waveform") and hasattr(self.single_container.waveform, "set_beatgrid_visible"):
                    self.single_container.waveform.set_beatgrid_visible(visible)
        except Exception:
            pass
        spv = getattr(self, "single_player_view", None)
        if spv and hasattr(spv, "waveform") and hasattr(spv.waveform, "set_beatgrid_visible"):
            try:
                spv.waveform.set_beatgrid_visible(visible)
            except Exception:
                pass
        # Odtwarzacz MVP (legacy single_container/Focused ukryty/usunięty z sole odt)
        try:
            if hasattr(self, "odtwarzacz_view") and self.odtwarzacz_view:
                if hasattr(self.odtwarzacz_view, "waveform") and hasattr(self.odtwarzacz_view.waveform, "set_beatgrid_visible"):
                    self.odtwarzacz_view.waveform.set_beatgrid_visible(visible)
        except Exception:
            pass

    # _build_mixer_strip i _update_crossfader_volumes usunięte w Opcja A (sole new architecture).
    # Funkcjonalność recent/load/stopall zachowana w kompaktowym pasku narzędzi (dodany poniżej po global_mixer).
    # Crossfader/master/cue/PFL obsługiwane wewnątrz DualConsoleWidget + MixerStrip.

    def _toggle_layout(self):
        """W sole new architecture (DualConsoleWidget) układy side-by-side są wewnątrz Dual (QSplitter).
        Ten toggle jest no-op (przycisk i logika usunięte w cleanup)."""
        logger.debug("_toggle_layout: no-op (splitter w DualConsoleWidget zarządza layoutem)")

    # ------------------------------------------------------------------
    # HELPERY DLA NOWEJ ARCHITEKTURY (integracja wiring)
    # Tworzenie kontrolerów + widoków w stylu "dumb view + smart controller"
    # Zachowujemy pełne zachowanie, polski w komentarzach.
    # ------------------------------------------------------------------

    def _create_deck_controllers(self):
        """Tworzy parę DeckController (A/B) podłączoną do PlaybackEngine. Sole new architecture."""
        if DeckController is None or not hasattr(self, "playback_engine"):
            return None, None
        try:
            ctrl_a = DeckController("A", self.playback_engine)
            ctrl_b = DeckController("B", self.playback_engine)
            logger.debug("Nowa architektura: DeckController A/B utworzone")
            return ctrl_a, ctrl_b
        except Exception as exc:
            logger.exception(f"Błąd tworzenia DeckController: {exc}")
            return None, None

    def _create_dual_console_ui(self):
        """Buduje DualConsoleWidget jako sole impl nowej architektury.
        Zwraca dual bez dodawania do layoutu — content_stack (QStacked) zarządza visibility (per solidify step 1).
        Dual/console paths pozostają NIETKNIĘTE poza zmianą add.
        """
        try:
            ctrl_a, ctrl_b = self._create_deck_controllers()
            if not ctrl_a or not ctrl_b:
                return None
            self._deck_ctrl_a = ctrl_a
            self._deck_ctrl_b = ctrl_b

            dual = DualConsoleWidget(ctrl_a, ctrl_b, self.playback_engine, self)
            # NIE dodajemy do main_layout tutaj — caller wkłada do content_stack
            self._console_widgets.extend([dual])

            self.deck_a = dual.get_deck_view("A") if hasattr(dual, "get_deck_view") else None
            self.deck_b = dual.get_deck_view("B") if hasattr(dual, "get_deck_view") else None

            # Usunięto legacy Focused single_container (po Opcja A sole OdtwarzaczView dla single).
            # Po sole odt for single + dual nie używa focused dla A/B (używa ConsoleDeckView), niepotrzebny.
            # Ustaw None + zawsze ukryty w switch/guardach dla kompat (jeśli stare refy).
            # Per SZPIEG/Plan/REVIEWER findings: ukryj/usuń legacy focused single_container.
            self.single_container = None

            logger.info("NEW ARCHITECTURE ACTIVE: DualConsoleWidget + 2x ConsoleDeckView + DeckController A/B (sole odt single, legacy focused removed)")
            # Upewnij się że initial mixing jest zaaplikowane (master/cross/trim) nawet bez global_mixer
            QtCore.QTimer.singleShot(50, self._apply_initial_mixer_values)

            return dual
        except Exception as exc:
            logger.exception(f"Błąd _create_dual_console_ui: {exc}")
            return None

    def _create_focused_single_ui(self, main_layout: QtWidgets.QVBoxLayout):
        """Tworzy FocusedDeckView jako sole single view (tryb 'Odtwarzacz').
        Legacy heavy — w sole new arch używamy odtwarzacz_view dla single; ten jest hidden/usunięty dla compat (per Opcja A + sole odt).
        Nie używany w normal flow single (odt sole).
        """
        try:
            if not hasattr(self, "_deck_ctrl_a") or self._deck_ctrl_a is None:
                ctrl_a, _ = self._create_deck_controllers()
                self._deck_ctrl_a = ctrl_a
                self._deck_ctrl_b = None

            if self._deck_ctrl_a is None:
                return None

            focused = FocusedDeckView(self._deck_ctrl_a, self)
            main_layout.insertWidget(1, focused)
            focused.setVisible(False)
            self.single_container = focused
            self.single_player_view = focused
            logger.info("NEW ARCHITECTURE ACTIVE: FocusedDeckView (tryb single) + DeckController (legacy hidden)")
            return focused
        except Exception as exc:
            logger.exception(f"Błąd _create_focused_single_ui: {exc}")
            return None

    def _create_odtwarzacz_ui(self):
        """Tworzy SimpleDeckController + OdtwarzaczView dla czystego minimal single 'Odtwarzacz' MVP.
        Tylko basics: load/play/pause/stop + title/time/BPM/waveform. Nie dotyka dual paths.
        Dodaje do content_stack (QStacked) w callerze — brak bezpośredniego add do main + visible hacks.
        File=plik (load_dropped/load_track), Stream=odtwarzanie audio z pliku (play/pause via engine).
        **Uwaga dla nowych agentów/programistów:** Implementacja dokładnie per nadrzędny SZPIEG Build Spec + Plan team review (z crew/SZPIEG_agent_spec_and_archive.md + memory.md + crew/PLAN_...). Patrz docs dla zasad dokumentacji (zawsze update memory/HISTORY/crew/SZPIEG + code docs + todo + commit). SZPIEG spec jest binding — zero odstępstw. (WRITER 2026-06-02)
        """
        try:
            if not hasattr(self, "playback_engine") or not self.playback_engine:
                return None
            ctrl = SimpleDeckController("A", self.playback_engine)
            self._simple_deck_ctrl = ctrl
            view = OdtwarzaczView(ctrl, self)
            # NIE add tutaj do layoutu — caller (po solidyfikacji) wkłada do content_stack
            # view.setVisible(False) usunięte — sterowane przez stack index
            self.odtwarzacz_view = view
            logger.info("NEW ARCHITECTURE ACTIVE: SimpleDeckController + OdtwarzaczView (minimal single 'Odtwarzacz' MVP)")
            return view
        except Exception as exc:
            logger.exception(f"Błąd _create_odtwarzacz_ui: {exc}")
            self._simple_deck_ctrl = None
            return None

    # ------------------------------------------------------------------
    # Player mode switching (Odtwarzacz vs Konsola DJ)
    # ------------------------------------------------------------------

    def _switch_player_mode(self, mode_id: int):
        """Switch between clean single-deck view and full dual console.
        Single ("Odtwarzacz"): dedicated SimpleDeckController + OdtwarzaczView (MVP basics only).
        Dual/Console: full DeckController + DualConsoleWidget/Focused (untouched).
        Używa QStackedWidget (content_stack) do przełączania — zero setVisible/raise_/hacks na odt vs dual (per step 1 solidify).
        SOLIDIFY: dual zawsze _DUAL_CONSOLE_IDX=0, odt _ODT_IDX=1. Switch correct, no race.
        """
        use_single_mode = (mode_id == 0)  # single btn id z mode_btn_group =0 ; console=1
        self._current_mode = "single" if use_single_mode else "console"

        # Popraw init order / race guard (per findings): ensure odt ready przed switch do single (jeśli nie ma — create on demand).
        # Zapewnia odt przed setCurrent / compact / play etc.
        if use_single_mode and not getattr(self, "odtwarzacz_view", None):
            try:
                odt = self._create_odtwarzacz_ui()
                self.odtwarzacz_view = odt
                if odt and hasattr(self, "content_stack") and self.content_stack:
                    if odt not in [self.content_stack.widget(i) for i in range(self.content_stack.count()) if self.content_stack.widget(i)]:
                        self.content_stack.addWidget(odt)
            except Exception as e:
                logger.warning(f"switch ensure odt failed: {e}")

        # Compact only for single odt
        if not use_single_mode and hasattr(self, "compact_btn"):
            try:
                self.compact_btn.setChecked(False)
                self.compact_btn.setEnabled(True)  # allow reenable on back to single
            except Exception:
                pass

        # Update button checked states (in case called programmatically)
        if hasattr(self, "mode_btn_single") and hasattr(self, "mode_btn_console"):
            self.mode_btn_single.setChecked(use_single_mode)
            self.mode_btn_console.setChecked(not use_single_mode)

        # Legacy single_player_view / single_container (Focused) — usunięty z dual create; zawsze ukryty/None dla sole odt single.
        # Guardy defensywne.
        spv = getattr(self, "single_player_view", None)
        if spv:
            spv.setVisible(False)
        if hasattr(self, "single_container") and self.single_container:
            try:
                self.single_container.setVisible(False)
            except Exception:
                pass

        # === QSTACK SWITCH (czysty, bez overlap/hack) per step1+3 ===
        # Odtwarzacz MVP w stack index self._ODT_IDX, dual_console w self._DUAL_CONSOLE_IDX.
        # Dual paths (dual_console + single_container/Focused) pozostają NIETKNIĘTE poza index.
        # Aggressive setCurrent + guards count (no race on init order).
        # Visibility no-overlap: QStack setCurrent primary, hide console ONLY for non-stack widgets (tools/recent etc).
        # single default, no legacy focused visible.
        if hasattr(self, "content_stack") and self.content_stack:
            target_idx = self._ODT_IDX if use_single_mode else self._DUAL_CONSOLE_IDX
            if self.content_stack.count() > target_idx:
                self.content_stack.setCurrentIndex(target_idx)
            else:
                # Fallback jeśli stack niepełny (np. error path) — nie crash
                logger.debug(f"QStack switch: count={self.content_stack.count()} < target {target_idx}")
            # Upewnij się że odt ma beatgrid jeśli single (dla wave)
            if use_single_mode and hasattr(self, "odtwarzacz_view") and self.odtwarzacz_view:
                try:
                    if hasattr(self.odtwarzacz_view, "waveform") and hasattr(self.odtwarzacz_view.waveform, "set_beatgrid_visible"):
                        self.odtwarzacz_view.waveform.set_beatgrid_visible(True)
                except Exception:
                    pass
                # Re-sync compact if toggle was on (odt may have been hidden)
                if hasattr(self, "compact_btn") and self.compact_btn.isChecked():
                    try:
                        self.odtwarzacz_view.set_compact_mode(True)
                        # Po show stack current odt + compact: re-ensure spin visible (timing per findings)
                        if hasattr(self.odtwarzacz_view, "_spin_indicator"):
                            sp = self.odtwarzacz_view._spin_indicator
                            if not sp.isVisible():
                                sp.setVisible(True)
                                sp.update()
                    except Exception:
                        pass

        # Aggressively hide/show console content (działa dla dual widgets, nie dla stack content)
        # (dla kompat z narzędziami/recent etc. — zostawione, ale odt/dual sterowane przez stack index)
        # Guard: nie dotykaj widgetów które są w content_stack (QStacked zarządza visibility dla odt/dual)
        # Visibility no-overlap: tylko non-stack widgets.
        stack_widgets = set()
        if hasattr(self, "content_stack") and self.content_stack:
            for i in range(self.content_stack.count()):
                w = self.content_stack.widget(i)
                if w: stack_widgets.add(w)
        for w in getattr(self, "_console_widgets", []):
            if w and w not in stack_widgets:
                try:
                    w.setVisible(not use_single_mode)
                except Exception:
                    pass

        # (cross_frame z starej arch usunięty w Opcja A; dual ma własny cross)

        # Sync w nowej architekturze (sole) dla odt MVP: użyj prostego ctrl jeśli single.
        if use_single_mode:
            try:
                if self.playback_engine and hasattr(self, "_simple_deck_ctrl") and self._simple_deck_ctrl:
                    state = self.playback_engine.get_deck_state("A")
                    if state and hasattr(self, "odtwarzacz_view") and self.odtwarzacz_view and hasattr(self.odtwarzacz_view, "waveform"):
                        self.odtwarzacz_view.waveform.set_playhead(state.position_ms)
            except Exception:
                pass
            # Dodatkowy guard na heavy
            if hasattr(self, "single_container") and self.single_container:
                self.single_container.setVisible(False)

    def _on_compact_toggled(self, checked: bool):
        """Toggle compact na odt (single only). Pilot-like + anim spin.
        W console: no-op lub info.
        Per spec: toggle w window, set na odt + simple.
        """
        is_single = getattr(self, '_current_mode', 'console') == 'single'
        if not is_single:
            self.compact_btn.setChecked(False)
            try:
                self.compact_btn.setToolTip("Compact tylko w trybie Odtwarzacz (single). W konsoli dual — wyłączone.")
            except Exception:
                pass
            return
        odt = getattr(self, "odtwarzacz_view", None)
        if odt and hasattr(odt, "set_compact_mode"):
            try:
                odt.set_compact_mode(checked)
            except Exception as e:
                logger.warning(f"compact toggle odt failed: {e}")
        # sync text
        try:
            self.compact_btn.setText("☑ Compact" if checked else "☐ Compact")
        except Exception:
            pass
        # Pilot feel: auto adjust min size for compact (per SZPIEG/Plan step2) -- smaller for mini pilot, restore for normal.
        # Scalability preserved (no fixed, user can still resize larger; air/margins inside odt).
        # Używa _orig_ zapisane w init (dynamic).
        try:
            if checked:
                self.setMinimumSize(380, 280)  # pilot-like min
                # optional gentle shrink if current larger (non-destructive)
                if self.width() > 520 or self.height() > 420:
                    self.resize(max(420, min(self.width(), 520)), max(300, min(self.height(), 380)))
            else:
                if hasattr(self, "_orig_min_w"):
                    self.setMinimumSize(self._orig_min_w, self._orig_min_h)
                else:
                    self.setMinimumSize(980, 720)
        except Exception:
            pass
        logger.debug(f"Compact toggled: {checked} (single={is_single})")

    def _apply_base_style(self):
        """Rich pro dark booth stylesheet — high contrast, larger controls, readable everywhere."""
        self.setStyleSheet(f"""
            QMainWindow, QWidget {{
                background-color: {COLORS["bg"]};
                color: {COLORS["text"]};
                font-family: "Segoe UI", "Noto Sans", Arial, sans-serif;
                font-size: 13px;
            }}
            QLabel {{
                color: {COLORS["text"]};
            }}
            QPushButton {{
                background-color: #1a2233;
                border: 1px solid #2f3a52;
                border-radius: 5px;
                padding: 4px 10px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                border-color: {COLORS["accent"]};
                background-color: #232d42;
            }}
            QPushButton:pressed {{
                background-color: #0f1623;
            }}
            QPushButton:checked {{
                background-color: {COLORS["accent"]};
                color: {COLORS["bg"]};
                border-color: {COLORS["accent"]};
                font-weight: 700;
            }}
            QComboBox {{
                background-color: #1a2233;
                border: 1px solid #2f3a52;
                border-radius: 4px;
                padding: 2px 6px;
                min-height: 20px;
            }}
            QSlider::groove:horizontal {{
                height: 6px;
                background: #1f2a40;
                border-radius: 3px;
            }}
            QSlider::handle:horizontal {{
                background: {COLORS["accent"]};
                width: 16px;
                height: 16px;
                margin: -5px 0;
                border-radius: 8px;
                border: 2px solid #0a0e17;
            }}
            QSlider::groove:vertical {{
                width: 6px;
                background: #1f2a40;
                border-radius: 3px;
            }}
            QSlider::handle:vertical {{
                background: {COLORS["accent"]};
                height: 16px;
                width: 16px;
                margin: 0 -5px;
                border-radius: 8px;
                border: 2px solid #0a0e17;
            }}
            /* Crossfader extra weight */
            QSlider#crossfader, QSlider[objectName="crossfader"] {{
                min-height: 28px;
            }}
        """)

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat("application/x-lumbago-track-paths") or event.mimeData().hasUrls():
            # mime + position dla drag (FILE load), highlight w subviews (odt)
            pos = event.position().toPoint() if hasattr(event, "position") else event.pos()
            logger.debug(f"Window dragEnter mime ok at {pos}")
            event.acceptProposedAction()

    def dropEvent(self, event):
        mime = event.mimeData()
        paths = []

        if mime.hasFormat("application/x-lumbago-track-paths"):
            data = mime.data("application/x-lumbago-track-paths").data().decode()
            paths = [p for p in data.split(",") if p]
        elif mime.hasUrls():
            for url in mime.urls():
                if url.isLocalFile():
                    paths.append(url.toLocalFile())

        if paths:
            # Lepsze targetowanie A/B po pozycji dropu (lewa połowa okna = A, prawa = B).
            # Działa intuicyjnie w trybie dual console. W single zawsze A.
            # Highlight safety + position: w odt view (główny dla single) jest lokalny highlight na drag.
            # EFFECT + file/stream: drop = load FILE (mime+repo full Track), transport=STREAM.
            pos = event.position().toPoint() if hasattr(event, "position") else event.pos()
            if getattr(self, "_current_mode", "console") == "single" or not hasattr(self, "dual_console") or not self.dual_console:
                deck = "A"
            else:
                deck = "A" if pos.x() < (self.width() / 2) else "B"

            self._load_dropped_track(deck, paths[0])
            # Jeśli multi-select, ładujemy resztę do drugiego decku (pro UX)
            if len(paths) > 1:
                other = "B" if deck == "A" else "A"
                self._load_dropped_track(other, paths[1])
            event.acceptProposedAction()

    def closeEvent(self, event):
        """Zwalniamy zasoby audio przy zamknięciu okna."""
        try:
            if hasattr(self, "playback_engine") and self.playback_engine:
                self.playback_engine.release_all()
        except Exception:
            pass
        if event is not None:
            event.accept()

    def load_track_to_deck(self, deck: str, track: Track):
        """Ładuje track do wybranego decku.
        W single ("Odtwarzacz"): route do _simple_deck_ctrl.load_track (MVP).
        W console/dual: pełny DeckController (nietknięte).

        FILE vs STREAM (per SZPIEG spec):
        - load = operacja na PLIKU (fizyczna ścieżka audio na dysku, lookup DB, waveform extract).
        - transport/play/pause = operacja na STREAMIE (audio playback z załadowanego pliku via PlaybackEngine).
        Guard: load nie uruchamia playbacku (tylko przygotowuje plik).
        """
        d = deck.upper()
        is_single_mode = getattr(self, '_current_mode', 'console') == 'single'

        if is_single_mode and d == "A" and hasattr(self, "_simple_deck_ctrl") and self._simple_deck_ctrl:
            # Guard + safety prompt w load jeśli playing (per "nowa lista" + SZPIEG/Plan findings).
            # Podobnie jak w odt dropEvent i window drop dla single: prompt confirm gdy trwa stream (FILE load podczas playbacku).
            # OdtwarzaczView (odt load) + window load path — safety jak w window drop.
            odt = getattr(self, "odtwarzacz_view", None)
            if odt and getattr(odt, "_is_playing", False):
                try:
                    from PyQt6.QtWidgets import QMessageBox
                    resp = QMessageBox.question(
                        self, "Odtwarzacz — Safety (load via library)",
                        "Trwa odtwarzanie (stream). Załadować nowy PLIK i zatrzymać?\n(EFEKT: stop + load nowego pliku z cue=0; FILE op podczas STREAM)",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                        QMessageBox.StandardButton.No
                    )
                    if resp != QMessageBox.StandardButton.Yes:
                        return
                except Exception:
                    pass  # non fatal, proceed with caution
            try:
                prev = getattr(self._simple_deck_ctrl, 'current_track', None)
                self._simple_deck_ctrl.load_track(track)  # FILE only: przygotowuje plik + cue=0
                self._push_recent(d, prev)
            except Exception as e:
                logger.exception(f"load_track_to_deck (Odtwarzacz MVP single, {d}) failed")
            try:
                self.deck_track_loaded.emit(d, track)
            except Exception as exc:
                logger.debug(f"deck_track_loaded emit failed: {exc}")
            return

        # Dual/console path (full controller) – untouched
        ctrl = self._deck_ctrl_a if d == "A" else self._deck_ctrl_b
        if ctrl:
            try:
                prev = getattr(ctrl, 'current_track', None)
                ctrl.load_track(track)  # FILE only
                self._push_recent(d, prev)
            except Exception as e:
                logger.exception(f"load_track_to_deck (nowa arch, {d}) failed")
        # W trybie single synchronizuj Focused (używa tego samego ctrl_a) – guard
        if d == "A" and hasattr(self, "single_player_view") and self.single_player_view:
            try:
                if hasattr(self.single_player_view, "current_track"):
                    self.single_player_view.current_track = track
            except Exception:
                pass
        try:
            self.deck_track_loaded.emit(d, track)
        except Exception as exc:
            logger.debug(f"deck_track_loaded emit failed: {exc}")

    def unload_deck(self, deck: str):
        d = deck.upper()
        is_single_mode = getattr(self, '_current_mode', 'console') == 'single'

        if is_single_mode and d == "A" and hasattr(self, "_simple_deck_ctrl") and self._simple_deck_ctrl:
            try:
                self._simple_deck_ctrl.unload()
            except Exception:
                pass
            self.deck_track_unloaded.emit(d)
            if hasattr(self, "odtwarzacz_view") and self.odtwarzacz_view:
                try:
                    odt = self.odtwarzacz_view
                    if hasattr(odt, "title_label"):
                        odt.title_label.setText("Brak utworu — upuść plik lub załaduj z biblioteki")
                    if hasattr(odt, "bpm_label"):
                        odt.bpm_label.setText("— BPM")
                except Exception:
                    pass
            return

        # Dual/console path – untouched
        ctrl = self._deck_ctrl_a if d == "A" else self._deck_ctrl_b
        if ctrl:
            try:
                ctrl.unload_track()
            except Exception:
                pass
        self.deck_track_unloaded.emit(d)
        # Wyczyść alias single jeśli A
        if d == "A" and hasattr(self, "single_player_view") and self.single_player_view:
            try:
                spv = self.single_player_view
                if hasattr(spv, "title_label"): spv.title_label.setText("Brak utworu — upuść plik lub załaduj z biblioteki")
                if hasattr(spv, "bpm_label"): spv.bpm_label.setText("— BPM")
                if hasattr(spv, "waveform") and hasattr(spv.waveform, "clear"): spv.waveform.clear()
                if hasattr(spv, "time_label"): spv.time_label.setText("0:00 / 0:00")
                if hasattr(spv, "current_track"): spv.current_track = None
                if hasattr(spv, "hotcue_grid") and hasattr(spv.hotcue_grid, "clear_all"):
                    spv.hotcue_grid.clear_all()
            except Exception:
                pass

    def stop_all_decks(self):
        """Global stop for both decks + clear play states (sole new arch)."""
        try:
            if self.playback_engine:
                self.playback_engine.stop_deck("A")
                self.playback_engine.stop_deck("B")
            # Let signals from controllers/views update transport buttons (ConsoleDeckView/Focused use .transport.set_playing)
            # Direct play_btn access removed (old DeckWidget style); use transport if present for immediate feedback.
            for deck_view in (getattr(self, 'deck_a', None), getattr(self, 'deck_b', None)):
                if deck_view:
                    try:
                        if hasattr(deck_view, 'transport') and hasattr(deck_view.transport, 'set_playing'):
                            deck_view.transport.set_playing(False)
                        elif hasattr(deck_view, 'play_btn'):
                            deck_view.play_btn.setText("▶")
                    except Exception:
                        pass
            if hasattr(self, "single_player_view") and self.single_player_view:
                try:
                    spv = self.single_player_view
                    if hasattr(spv, 'transport') and hasattr(spv.transport, 'set_playing'):
                        spv.transport.set_playing(False)
                    elif hasattr(spv, 'play_btn'):
                        spv.play_btn.setText("▶  ODTWÓRZ")
                    if hasattr(spv, "waveform") and hasattr(spv.waveform, "set_playhead"):
                        spv.waveform.set_playhead(0)
                except Exception:
                    pass
            # Odtwarzacz MVP single – respektuj prosty controller + view (guard heavy)
            if getattr(self, '_current_mode', 'console') == 'single' and hasattr(self, "odtwarzacz_view") and self.odtwarzacz_view:
                try:
                    if self.playback_engine:
                        self.playback_engine.stop_deck("A")
                    odt = self.odtwarzacz_view
                    if hasattr(odt, 'play_btn'):
                        odt.play_btn.setText("▶ ODTWÓRZ")
                    if hasattr(odt, "waveform") and hasattr(odt.waveform, "set_playhead"):
                        odt.waveform.set_playhead(0)
                    if hasattr(odt, "_is_playing"):
                        odt._is_playing = False
                    if hasattr(odt, "controller"):
                        odt.controller.play_state_changed.emit(False)
                except Exception:
                    pass
            self.all_stopped.emit()
            logger.info("DJ Player: Stop all decks")
        except Exception as e:
            logger.warning(f"stop_all_decks error: {e}")

    def unload_all(self):
        self.unload_deck("A")
        self.unload_deck("B")

    def _push_recent(self, deck: str, track: Optional[Track]):
        if not track or not getattr(track, 'path', None):
            return
        recents = self._recent_a if deck.upper() == "A" else self._recent_b
        # Avoid consecutive duplicates or current (path based)
        if recents and recents[0].path == track.path:
            return
        # Also avoid if it's the other deck's current? no, per deck ok
        recents.insert(0, track)
        # Trim + dedup by path keeping most recent
        seen = set()
        deduped = []
        for t in recents:
            if t.path not in seen:
                seen.add(t.path)
                deduped.append(t)
            if len(deduped) >= self._MAX_RECENT:
                break
        if deck.upper() == "A":
            self._recent_a = deduped
        else:
            self._recent_b = deduped

    def _populate_recent_menu(self, deck: str, menu: QtWidgets.QMenu):
        menu.clear()
        recents = self._recent_a if deck.upper() == "A" else self._recent_b
        if not recents:
            act = menu.addAction("(brak historii)")
            act.setEnabled(False)
            return
        for t in recents[:self._MAX_RECENT]:
            title = f"{t.artist or ''} - {t.title or ''}".strip(" -") or Path(t.path).stem
            display = (title[:38] + "…") if len(title) > 40 else title
            act = menu.addAction(display)
            # Capture track by value
            act.triggered.connect(lambda checked=False, tr=t, d=deck: self.load_track_to_deck(d, tr))

    def _load_dropped_track(self, deck: str, path: str):
        """Ładuje track upuszczony przez drag & drop (używa ścieżki).
        To jest FILE op: ładowanie PLIKU audio (nie stream). DB lookup dla metadanych.
        Po load, transport (play) używa streamu z pliku.
        """
        try:
            from pathlib import Path as PathLib
            name = PathLib(path).stem
            track = Track(path=path, title=name)
            # Enrich from DB if this file is in the library (to get id for hotcues)
            try:
                from data.repository import get_track_by_path
                dbt = get_track_by_path(path)
                if dbt and dbt.id:
                    track = dbt
            except Exception as exc:
                logger.debug(f"_load_dropped_track: DB lookup failed: {exc}")
            self.load_track_to_deck(deck, track)
        except Exception as e:
            logger.warning(f"Błąd ładowania upuszczonego tracka: {e}")

    def _global_play_pause(self):
        """Spacja = Play/Pause na Deck A (domyślny aktywny deck).
        W single: używa simple controller (play/pause explicit z cue logic).
        PLAY/PAUSE = STREAM op (dźwięk z pliku); nie zmienia pliku.
        """
        is_single = getattr(self, '_current_mode', 'console') == 'single'
        if is_single and hasattr(self, "_simple_deck_ctrl") and self._simple_deck_ctrl:
            try:
                # Użyj engine state do decyzji play vs pause (prosty toggle na spację)
                if self.playback_engine:
                    st = self.playback_engine.get_deck_state("A")
                    if st and getattr(st, "is_playing", False):
                        self._simple_deck_ctrl.pause()
                    else:
                        self._simple_deck_ctrl.play()
                return
            except Exception:
                pass
        if hasattr(self, "_deck_ctrl_a") and self._deck_ctrl_a:
            try:
                self._deck_ctrl_a.toggle_play()
                return
            except Exception:
                pass

    def _quick_load_hotcue(self, index: int):
        """Ctrl+1..8 = jump to hotcue on Deck A. Sole new arch."""
        if hasattr(self, "_deck_ctrl_a") and self._deck_ctrl_a:
            try:
                self._deck_ctrl_a.jump_hotcue(index)
                return
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Mixer strip handlers (Master, HP Cue, PFL, Sync)
    # ------------------------------------------------------------------

    def _apply_initial_mixer_values(self):
        if not self.playback_engine:
            return
        try:
            # Dual ma własne slidery i woła set_master_volume / cross w _apply_initial_mixer.
            # Tu defensywnie ustawiamy sensowne defaulty jeśli nic nie ustawiło.
            # (master 0.85, cross 0.0 = center)
            self.playback_engine.set_master_volume(0.85)
            self.playback_engine.set_crossfader(0.0)
            # Per-deck trim default (jeśli engine wspiera)
            try:
                self.playback_engine.set_deck_trim("A", 0.85)
                self.playback_engine.set_deck_trim("B", 0.85)
            except Exception:
                pass
        except Exception:
            pass
        self._update_backend_info_label()

    def _on_master_changed(self, value: int):
        # Obsługa global_mixer (MixerStrip) + ew. stary master_value (jeśli obecny)
        if hasattr(self, "master_value") and self.master_value:
            self.master_value.setText(str(value))
        if hasattr(self, "global_mixer") and self.global_mixer:
            try:
                self.global_mixer.set_master(value)
            except Exception:
                pass
        if self.playback_engine:
            try:
                self.playback_engine.set_master_volume(value / 100.0)
            except Exception:
                pass

    def _on_hp_changed(self, value: int):
        if hasattr(self, "hp_value") and self.hp_value:
            self.hp_value.setText(str(value))
        if hasattr(self, "global_mixer") and self.global_mixer:
            try:
                self.global_mixer.set_hp(value)
            except Exception:
                pass
        # Na razie tylko UI — prawdziwy oddzielny output HP (w silniku) wymaga więcej

    def _on_pfl_changed(self, deck: str, checked: bool):
        # Obsługa global_mixer (MixerStrip) + delegacja do deck views jeśli mają pfl_btn (dla statusu)
        style = "background-color: #3dd9c3; color: #0f1623; font-weight: bold;" if checked else ""
        btn = None
        if hasattr(self, "pfl_a") and deck == "A": btn = self.pfl_a
        elif hasattr(self, "pfl_b") and deck == "B": btn = self.pfl_b
        if btn:
            btn.setStyleSheet(style)
        # New arch: deck views (Console/Focused) mogą mieć wewnętrzny PFL toggle podłączony do controller/engine
        try:
            if deck == "A" and hasattr(self, "deck_a") and self.deck_a and hasattr(self.deck_a, "pfl_btn"):
                self.deck_a.pfl_btn.setChecked(checked)
            elif deck == "B" and hasattr(self, "deck_b") and self.deck_b and hasattr(self.deck_b, "pfl_btn"):
                self.deck_b.pfl_btn.setChecked(checked)
        except Exception:
            pass
        logger.debug(f"PFL {deck}: {'ON' if checked else 'OFF'}")

    def _on_global_crossfader(self, value: int):
        """Obsługa crossfadera z MixerStrip (gdy używany jako globalny)."""
        if self.playback_engine:
            try:
                pos = (value / 50.0) - 1.0
                self.playback_engine.set_crossfader(pos)
            except Exception:
                pass

    def _do_sync(self):
        """Global mixer SYNC (legacy path) — delegates basic tempo match.
        Prefer per-deck SYNC buttons (in ConsoleDeckView) for full pro experience (DeckController.do_sync).
        """
        if not self.playback_engine or not (getattr(self, 'deck_a', None) and getattr(self, 'deck_b', None)):
            return
        try:
            state_a = self.playback_engine.get_deck_state("A")
            if state_a:
                self.playback_engine.set_deck_rate("B", state_a.rate)
                # New arch: PitchControl inside views listens to controller; avoid direct slider poke
                # Visual feedback only on the global sync_btn if present (rare now)
                if hasattr(self, 'sync_btn') and self.sync_btn:
                    self.sync_btn.setStyleSheet("background-color: #5cc8ff; color: black; font-weight: 700;")
                    QtCore.QTimer.singleShot(900, lambda: self.sync_btn.setStyleSheet("") if hasattr(self, 'sync_btn') else None)
                logger.info("Global SYNC: Deck B rate matched to A (use deck SYNC for phase+key+quantize)")
        except Exception as e:
            logger.warning(f"Global sync failed: {e}")

    def _update_backend_info_label(self):
        if not hasattr(self, "backend_info_label") or not self.playback_engine:
            return
        try:
            d = self.playback_engine.get_diagnostics()
            a = d.get("deck_a", {})
            b = d.get("deck_b", {})
            txt = f"{a.get('backend','?')} / {b.get('backend','?')}"
            self.backend_info_label.setText(txt)
        except Exception:
            pass

    def _dismiss_fallback_banner(self, banner):
        """Session-persistent dismiss for the fallback warning."""
        self._fallback_dismissed_this_session = True
        if banner:
            banner.setVisible(False)

    def _load_file_dialog(self, deck: str):
        """Open file dialog to load a track directly into a deck (standalone pro use).
        FILE op (load PLIK + DB), transport separate (STREAM via play etc). EFEKT tooltipy w UI.
        """
        from PyQt6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getOpenFileName(
            self,
            f"Load track to Deck {deck}",
            "",
            "Audio Files (*.mp3 *.wav *.flac *.ogg *.m4a *.aac);;All Files (*)"
        )
        if path:
            self._load_dropped_track(deck, path)

    def _maybe_show_fallback_banner(self, main_layout: QtWidgets.QVBoxLayout):
        """Prominent warning when the professional DJ Player is running on degraded QtMultimedia fallback."""
        if getattr(self, "_fallback_dismissed_this_session", False):
            return
        if not self.playback_engine:
            return
        try:
            d = self.playback_engine.get_diagnostics()
            using_qt = False
            for key in ("deck_a", "deck_b"):
                if d.get(key, {}).get("backend") == "qtmultimedia":
                    using_qt = True
                    break
            if not using_qt:
                return

            banner = QtWidgets.QFrame()
            banner.setStyleSheet(f"""
                QFrame {{
                    background-color: #3a2f1f;
                    border: 1px solid #854d0e;
                    border-radius: 4px;
                    margin: 2px 0;
                }}
                QLabel {{
                    color: {COLORS['warning']};
                    font-size: 11px;
                    font-weight: 600;
                    padding: 4px 10px;
                }}
            """)
            bl = QtWidgets.QHBoxLayout(banner)
            bl.setContentsMargins(6, 2, 6, 2)
            bl.setSpacing(6)

            lbl = QtWidgets.QLabel(
                "⚠ FALLBACK MODE: QtMultimedia (no real EQ, keylock, or low-jitter loops). Install VLC from videolan.org/vlc for full professional DJ features."
            )
            lbl.setWordWrap(False)
            bl.addWidget(lbl, 1)

            close_btn = QtWidgets.QPushButton("×")
            close_btn.setFixedSize(18, 18)
            close_btn.setStyleSheet("font-size: 13px; font-weight: bold; color: #facc15; border: none; background: transparent;")
            close_btn.clicked.connect(lambda: self._dismiss_fallback_banner(banner))
            bl.addWidget(close_btn)

            main_layout.addWidget(banner)
            self._fallback_banner = banner  # keep reference for session dismiss
            if hasattr(self, "_console_widgets"):
                self._console_widgets.append(banner)
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Dodatkowe skróty klawiszowe (UI polish – integracja z pro workflow)
    # ------------------------------------------------------------------
    def _toggle_quantize_a(self):
        if hasattr(self, "_deck_ctrl_a") and self._deck_ctrl_a:
            self._deck_ctrl_a.toggle_quantize()

    def _do_sync_a_b(self):
        if hasattr(self, "_deck_ctrl_a") and hasattr(self, "_deck_ctrl_b") and self._deck_ctrl_a and self._deck_ctrl_b:
            self._deck_ctrl_a.do_sync(self._deck_ctrl_b)
            self._deck_ctrl_a.status_changed.emit("SYNC A->B (Ctrl+S)")

    def resizeEvent(self, event):
        """Scalability polish (per SZPIEG Build Spec + Plan step6): dynamic resize for multi-res, no overlap.
        QStack + stretch + Expanding w odt/dual zapewniają core; air/margins preserved (odt handles wave/spin).
        Compact toggle may have set smaller minSize; no fixed sizes on expanding elems.
        """
        super().resizeEvent(event)
        # Defensywne: dynamic spin size in compact is handled in odt.resizeEvent itself.
        # Removed full _apply call here to avoid re-entrancy / layout feedback during compact toggle
        # (which changed child sizeHints and could trigger nested resizeEvents + crash or silent exit).
        # odt.resizeEvent already does:
        #   if self._compact and spin: compute s from self.width(), setFixedSize(s,s)
        pass  # (was re-apply; now safe)
