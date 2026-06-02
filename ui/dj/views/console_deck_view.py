"""
ui/dj/views/console_deck_view.py

ConsoleDeckView – bogaty, profesjonalny pojedynczy deck w trybie Dual Console ("Konsola DJ").

Zgodny z sekcją 5 dokumentu AGENT3 (opcja side-by-side Rekordbox-like):
- Nagłówek z wyraźną etykietą DECK A/B + tytuł + ogromny BPM
- Waveform (min 200px) + beatgrid
- Transport + TRIM + PITCH w jednym wierszu (pro layout)
- Przyciski KEY / SYNC / PFL / Q
- Pełny 3-pasmowy EQStrip (pionowe suwaki 100px)
- 8 dużych hotcue padów 78-82px
- Memory S/R + podstawowe Loop (IN/OUT/LOOP)
- Dużo kontrastu, booth-friendly rozmiary

WIDOK "DUMB":
- Kompozycja wyłącznie z małych widgetów + WaveformWidget + EQStrip + PitchControl + ręczne Trim/Loop/Memory
- Cała logika (playback, hotcue, snap, memory, EQ, pitch, sync) – wyłącznie DeckController
- Zero duplikacji – widoki A i B w DualConsoleWidget używają identycznej klasy

Zachowuje 100% zachowań:
- Waveform: click=seek, Shift+click=ustaw wolny hotcue, double-click=main cue preview
- Hotcue: lewy=skok (z Ctrl=kasuj), prawy=nadpisz
- Memory S/R, quantize Q, SYNC (z partnerem), KEYLOCK, EQ, TRIM, PITCH

Używa TYLKO helperów ze styles.py (BOOTH_COLORS, BOOTH_SIZES, get_*_stylesheet).
Pełne polskie komentarze/docstringi.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from PyQt6 import QtCore, QtWidgets

from core.models import Track
from ui.dj.deck_controller import DeckController
from ui.dj.views.hotcue_grid import HotcuePadGrid
from ui.dj.views.transport_bar import TransportBar
from ui.dj.views.pitch_control import PitchControl
from ui.dj.views.eq_strip import EQStrip
from ui.dj.styles import (
    BOOTH_SIZES,
    get_deck_panel_stylesheet,
    get_bpm_label_stylesheet,
    get_section_label_stylesheet,
    get_time_label_stylesheet,
    get_value_label_stylesheet,
    get_slider_stylesheet,
)

# WaveformWidget extracted (ui/dj/views/waveform_widget.py)
try:
    from ui.dj.views.waveform_widget import WaveformWidget
except Exception:  # pragma: no cover
    WaveformWidget = None  # type: ignore


def _format_ms(ms: int | None) -> str:
    if ms is None or ms < 0:
        return "0:00"
    total = max(0, int(ms)) // 1000
    m = total // 60
    s = total % 60
    return f"{m}:{s:02d}"


class ConsoleDeckView(QtWidgets.QFrame):
    """
    Profesjonalny deck konsolowy (używany jako para A+B w DualConsoleWidget).

    Tworzenie:
        deck_a = ConsoleDeckView(controller_a)
        deck_b = ConsoleDeckView(controller_b)
        deck_a.set_partner_controller(controller_b)  # dla SYNC
        deck_b.set_partner_controller(controller_a)

    Po stworzeniu widok automatycznie podłącza wszystkie sygnały.
    """

    def __init__(
        self,
        controller: DeckController,
        deck_label: str = "A",
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.controller = controller
        self.deck_label = deck_label
        self._current_duration_ms: int = 0
        self._last_playhead_ms: int = 0
        self._partner: DeckController | None = None

        self.setObjectName("DeckPanel")
        self.setStyleSheet(get_deck_panel_stylesheet())

        self.setAcceptDrops(True)  # drag&drop z biblioteki bezpośrednio na deck (Rekordbox-like)

        self._setup_ui()
        self._connect_controller_signals()
        self._connect_widget_signals()

        if hasattr(self, "status_label"):
            self.status_label.setText(f"DECK {deck_label} – gotowy")

    # ------------------------------------------------------------------
    # Layout (bogatszy niż Focused – pełny pro setup)
    # ------------------------------------------------------------------
    def _setup_ui(self) -> None:
        main = QtWidgets.QVBoxLayout(self)
        main.setContentsMargins(16, 14, 16, 14)
        main.setSpacing(14)

        # === HEADER: DECK LABEL + Tytuł + BPM ===
        header = QtWidgets.QHBoxLayout()
        header.setSpacing(8)

        self.deck_badge = QtWidgets.QLabel(self.deck_label)
        self.deck_badge.setStyleSheet(
            f"""
            color: #00e0ff;
            font-size: 20px;
            font-weight: 900;
            letter-spacing: 2px;
            min-width: 32px;
            background-color: #0f141c;
            border: 1px solid #3a4556;
            border-radius: 4px;
            padding: 2px 8px;
            """
        )
        self.deck_badge.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        self.title_label = QtWidgets.QLabel("Brak utworu")
        self.title_label.setStyleSheet("font-size: 15px; font-weight: 700; color: #f0f4f8;")
        self.title_label.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Preferred
        )

        self.bpm_label = QtWidgets.QLabel("— BPM")
        self.bpm_label.setStyleSheet(get_bpm_label_stylesheet())
        self.bpm_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter)
        self.bpm_label.setMinimumWidth(96)

        header.addWidget(self.deck_badge, 0)
        header.addWidget(self.title_label, 1)
        header.addWidget(self.bpm_label, 0)
        main.addLayout(header)

        # === WAVEFORM (min 200px) ===
        if WaveformWidget is not None:
            self.waveform = WaveformWidget()
        else:
            self.waveform = QtWidgets.QLabel("[Waveform]")
        self.waveform.setMinimumHeight(BOOTH_SIZES["waveform_min_height_console"])
        self.waveform.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding
        )
        main.addWidget(self.waveform, 5)

        # PPM menu kontekstowe (spójne z Focused)
        self.waveform.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.waveform.customContextMenuRequested.connect(self._show_waveform_context_menu)

        # === CZAS ===
        self.time_label = QtWidgets.QLabel("0:00 / 0:00")
        self.time_label.setStyleSheet(get_time_label_stylesheet())
        self.time_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        main.addWidget(self.time_label, 0)

        # === TRANSPORT + TRIM + PITCH (jeden wiersz pro) ===
        mix_row = QtWidgets.QHBoxLayout()
        mix_row.setSpacing(12)

        self.transport = TransportBar()
        mix_row.addWidget(self.transport, 0)

        # TRIM
        trim_col = QtWidgets.QVBoxLayout()
        trim_col.setSpacing(2)
        t_lbl = QtWidgets.QLabel("TRIM")
        t_lbl.setStyleSheet(get_section_label_stylesheet())
        trim_col.addWidget(t_lbl)
        self.trim_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.trim_slider.setRange(0, 100)
        self.trim_slider.setValue(85)
        self.trim_slider.setStyleSheet(get_slider_stylesheet("horizontal"))
        self.trim_slider.setFixedWidth(BOOTH_SIZES.get("pitch_slider_width", 160))
        self.trim_slider.valueChanged.connect(self._on_trim_changed)
        trim_col.addWidget(self.trim_slider)
        mix_row.addLayout(trim_col, 1)

        # PITCH + KEYLOCK (gotowy widget)
        self.pitch_control = PitchControl()
        mix_row.addWidget(self.pitch_control, 2)

        main.addLayout(mix_row, 0)

        # === PRO KONTROLKI: KEY/SYNC/PFL/Q (KEY jest w PitchControl) ===
        pro_row = QtWidgets.QHBoxLayout()
        pro_row.setSpacing(8)

        self.sync_btn = QtWidgets.QPushButton("SYNC")
        self.sync_btn.setFixedSize(54, 30)
        self.sync_btn.setCheckable(True)
        self.sync_btn.setStyleSheet(get_section_label_stylesheet().replace("10px", "11px"))

        self.pfl_btn = QtWidgets.QPushButton("PFL")
        self.pfl_btn.setFixedSize(46, 30)
        self.pfl_btn.setCheckable(True)
        self.pfl_btn.setStyleSheet(get_section_label_stylesheet().replace("10px", "11px"))
        self.pfl_btn.clicked.connect(self._on_pfl_toggled)

        # Krok 6: menu PPM dla SYNC i PFL
        self.sync_btn.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.pfl_btn.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.sync_btn.customContextMenuRequested.connect(self._show_sync_menu)
        self.pfl_btn.customContextMenuRequested.connect(self._show_pfl_btn_menu)

        self.quantize_btn = QtWidgets.QPushButton("Q")
        self.quantize_btn.setCheckable(True)
        self.quantize_btn.setChecked(True)
        self.quantize_btn.setFixedSize(42, 30)
        self.quantize_btn.setStyleSheet(get_section_label_stylesheet().replace("10px", "11px"))
        self.quantize_btn.clicked.connect(self._on_quantize_toggled)

        pro_row.addStretch(1)
        pro_row.addWidget(self.sync_btn, 0)
        pro_row.addWidget(self.pfl_btn, 0)
        pro_row.addWidget(self.quantize_btn, 0)
        main.addLayout(pro_row, 0)

        # === EQ + HOT CUES (EQ po lewej, pady po prawej – klasyczny układ) ===
        eq_hc = QtWidgets.QHBoxLayout()
        eq_hc.setSpacing(14)

        # EQ
        eq_col = QtWidgets.QVBoxLayout()
        eq_lbl = QtWidgets.QLabel("EQ")
        eq_lbl.setStyleSheet(get_section_label_stylesheet())
        eq_col.addWidget(eq_lbl)
        self.eq_strip = EQStrip()
        eq_col.addWidget(self.eq_strip)
        eq_hc.addLayout(eq_col, 0)

        # Hotcues
        hc_col = QtWidgets.QVBoxLayout()
        hc_lbl = QtWidgets.QLabel("HOT CUES")
        hc_lbl.setStyleSheet(get_section_label_stylesheet())
        hc_col.addWidget(hc_lbl)
        self.hotcue_grid = HotcuePadGrid(
            pad_size=BOOTH_SIZES.get("hotcue_pad", (82, 62))  # full booth size (Rekordbox polish; splitter handles)
        )
        hc_col.addWidget(self.hotcue_grid)
        eq_hc.addLayout(hc_col, 1)

        main.addLayout(eq_hc, 0)

        # === MEMORY + LOOP (dolny rząd) ===
        mem_loop = QtWidgets.QHBoxLayout()
        mem_loop.setSpacing(8)

        self.mem_s_btn = QtWidgets.QPushButton("S")
        self.mem_s_btn.setFixedSize(32, 26)
        self.mem_s_btn.setToolTip("Save Memory (hotcues + pitch + trim + loop + keylock)")

        self.mem_r_btn = QtWidgets.QPushButton("R")
        self.mem_r_btn.setFixedSize(32, 26)
        self.mem_r_btn.setToolTip("Recall Memory")

        # Krok 6: menu PPM dla memory
        self.mem_s_btn.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.mem_r_btn.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.mem_s_btn.customContextMenuRequested.connect(self._show_memory_menu)
        self.mem_r_btn.customContextMenuRequested.connect(self._show_memory_menu)

        self.loop_in_btn = QtWidgets.QPushButton("IN")
        self.loop_in_btn.setFixedSize(40, 26)
        self.loop_out_btn = QtWidgets.QPushButton("OUT")
        self.loop_out_btn.setFixedSize(44, 26)
        self.loop_toggle_btn = QtWidgets.QPushButton("LOOP")
        self.loop_toggle_btn.setFixedSize(52, 26)
        self.loop_toggle_btn.setCheckable(True)

        mem_loop.addWidget(QtWidgets.QLabel("MEM"), 0)
        mem_loop.addWidget(self.mem_s_btn, 0)
        mem_loop.addWidget(self.mem_r_btn, 0)
        mem_loop.addSpacing(16)
        mem_loop.addWidget(QtWidgets.QLabel("LOOP"), 0)
        mem_loop.addWidget(self.loop_in_btn, 0)
        mem_loop.addWidget(self.loop_out_btn, 0)
        mem_loop.addWidget(self.loop_toggle_btn, 0)

        # Krok 6: indywidualne menu PPM dla loop buttons
        for btn in (self.loop_in_btn, self.loop_out_btn, self.loop_toggle_btn):
            btn.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.loop_in_btn.customContextMenuRequested.connect(lambda p: self._show_loop_menu(p, "IN"))
        self.loop_out_btn.customContextMenuRequested.connect(lambda p: self._show_loop_menu(p, "OUT"))
        self.loop_toggle_btn.customContextMenuRequested.connect(lambda p: self._show_loop_menu(p, "LOOP"))
        mem_loop.addStretch(1)

        main.addLayout(mem_loop, 0)

        # Status
        self.status_label = QtWidgets.QLabel("")
        self.status_label.setStyleSheet("color:#6b7688; font-size:9px; font-weight:600;")
        self.status_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        main.addWidget(self.status_label, 0)

    # ------------------------------------------------------------------
    # Sygnały widgetów → kontroler
    # ------------------------------------------------------------------
    def _connect_widget_signals(self) -> None:
        # Transport
        self.transport.play_clicked.connect(self.controller.toggle_play)
        self.transport.cue_clicked.connect(self._on_cue_clicked)
        self.transport.stop_clicked.connect(self._on_stop_clicked)

        # Pitch / Keylock
        self.pitch_control.pitch_changed.connect(self.controller.set_pitch)
        self.pitch_control.keylock_toggled.connect(self.controller.set_keylock)

        # EQ
        self.eq_strip.eq_changed.connect(self.controller.set_eq)

        # Hotcues
        self.hotcue_grid.pad_activated.connect(self.controller.jump_hotcue)
        self.hotcue_grid.pad_set_requested.connect(self.controller.set_hotcue)
        self.hotcue_grid.pad_delete_requested.connect(self.controller.delete_hotcue)
        self.hotcue_grid.pad_rename_requested.connect(self._request_hotcue_rename)
        self.hotcue_grid.pad_color_change_requested.connect(self.controller.set_hotcue_color)

        # Memory
        self.mem_s_btn.clicked.connect(self.controller.save_memory)
        self.mem_r_btn.clicked.connect(self.controller.recall_memory)

        # Loop buttons (proste – używają ostatniej znanej pozycji playhead)
        self.loop_in_btn.clicked.connect(self._set_loop_in)
        self.loop_out_btn.clicked.connect(self._set_loop_out)
        self.loop_toggle_btn.clicked.connect(self._toggle_loop)

        # Waveform – identyczne zachowanie jak w Focused
        if WaveformWidget is not None and hasattr(self.waveform, "seek_requested"):
            self.waveform.seek_requested.connect(self.controller.seek)
            self.waveform.cue_set_requested.connect(self._handle_waveform_shift_click)
            self.waveform.double_clicked.connect(self._handle_waveform_double_click)

    def _on_cue_clicked(self) -> None:
        self.controller.seek(0)
        self.controller.status_changed.emit("CUE")

    def _on_stop_clicked(self) -> None:
        if self.controller.playback_engine:
            try:
                self.controller.playback_engine.stop_deck(self.controller.deck_id)
            except Exception:
                pass
        self.controller.play_state_changed.emit(False)
        self.controller.playhead_changed.emit(0)

    def _on_trim_changed(self, value: int) -> None:
        self.controller.set_trim(value / 100.0)

    def _on_quantize_toggled(self, _checked: bool) -> None:
        self.controller.toggle_quantize()

    def _on_pfl_toggled(self, checked: bool) -> None:
        # PFL to głównie wizualny status w tej fazie (pełne audio PFL w silniku później)
        self.controller.status_changed.emit("PFL ON" if checked else "PFL OFF")

    def _set_loop_in(self) -> None:
        self._loop_in_candidate = self._last_playhead_ms
        self.controller.status_changed.emit(f"IN @ {_format_ms(self._last_playhead_ms)}")

    def _set_loop_out(self) -> None:
        if hasattr(self, "_loop_in_candidate") and self._loop_in_candidate is not None:
            start = self._loop_in_candidate
            end = self._last_playhead_ms
            if end > start:
                self.controller.set_loop_points(start, end)
                self.controller.status_changed.emit("LOOP POINTS SET")
            else:
                self.controller.status_changed.emit("OUT musi być > IN")
        else:
            self.controller.status_changed.emit("Najpierw ustaw IN")

    def _toggle_loop(self, checked: bool) -> None:
        if checked:
            # Włącz istniejące punkty (jeśli są)
            if hasattr(self.controller, "_loop_in_ms") and self.controller._loop_in_ms is not None:
                self.controller.set_loop_points(self.controller._loop_in_ms, self.controller._loop_out_ms)
        else:
            self.controller.set_loop_points(None, None)

    def _handle_waveform_shift_click(self, time_ms: int) -> None:
        if not self.controller.current_track:
            return
        for idx in range(8):
            if self.controller.get_hotcue(idx) is None:
                self.controller.set_hotcue(idx)
                return
        self.controller.set_hotcue(0)

    def _handle_waveform_double_click(self, time_ms: int) -> None:
        snapped = self.controller.snap_to_beat(time_ms)
        self.controller.seek(snapped)
        self.controller.status_changed.emit("CUE SET (wave)")

    def _request_hotcue_rename(self, index: int) -> None:
        """Proste okno do zmiany nazwy hotcue."""
        current = ""
        cue = self.controller.get_hotcue(index)
        if cue and hasattr(cue, "label") and cue.label:
            current = cue.label

        text, ok = QtWidgets.QInputDialog.getText(
            self, "Zmień nazwę hotcue", "Nowa nazwa:", QtWidgets.QLineEdit.EchoMode.Normal, current
        )
        if ok:
            self.controller.set_hotcue_label(index, text.strip() or None)

    def _show_loop_menu(self, pos: QtCore.QPoint, which: str) -> None:
        """Indywidualne menu dla przycisków loop."""
        menu = QtWidgets.QMenu(self)
        if which == "IN":
            menu.addAction("Ustaw Loop In w aktualnej pozycji")
            menu.addAction("Wyczyść Loop In")
        elif which == "OUT":
            menu.addAction("Ustaw Loop Out w aktualnej pozycji")
            menu.addAction("Wyczyść Loop Out")
        else:
            menu.addAction("Włącz/Wyłącz LOOP")
            menu.addAction("Wyczyść loop")
            menu.addAction("Podwój długość loopa")
            menu.addAction("Pół długości loopa")
        menu.exec(self.loop_in_btn.mapToGlobal(pos) if which == "IN" else self.loop_out_btn.mapToGlobal(pos) if which == "OUT" else self.loop_toggle_btn.mapToGlobal(pos))

    def _show_memory_menu(self, pos: QtCore.QPoint) -> None:
        """Menu dla S/R memory."""
        menu = QtWidgets.QMenu(self)
        menu.addAction("Zapisz aktualny stan (Memory Save)")
        menu.addAction("Przywołaj ostatni zapis (Memory Recall)")
        menu.addSeparator()
        menu.addAction("Wyczyść pamięć")
        menu.exec(self.mem_s_btn.mapToGlobal(pos))

    def _show_sync_menu(self, pos: QtCore.QPoint) -> None:
        menu = QtWidgets.QMenu(self)
        menu.addAction("Wymuś resync")
        menu.addAction("Włącz/Wyłącz Auto-Sync")
        menu.exec(self.sync_btn.mapToGlobal(pos))

    def _show_pfl_btn_menu(self, pos: QtCore.QPoint) -> None:
        menu = QtWidgets.QMenu(self)
        menu.addAction("Toggle PFL")
        menu.addAction("Ustaw głośność cue")
        menu.exec(self.pfl_btn.mapToGlobal(pos))

    def _show_waveform_context_menu(self, pos: QtCore.QPoint) -> None:
        """Menu kontekstowe PPM na waveformie – z precyzyjną pozycją kliknięcia."""
        if not self.controller or not self.controller.current_track:
            return
        if not hasattr(self.waveform, "time_at_x"):
            return

        local_pos = self.waveform.mapFromGlobal(pos)
        click_ms = self.waveform.time_at_x(local_pos.x())

        menu = QtWidgets.QMenu(self)

        act_cue = menu.addAction("Ustaw CUE tutaj")
        act_hotcue_free = menu.addAction("Ustaw Hotcue (pierwszy wolny)")
        menu.addSeparator()

        hotcue_menu = menu.addMenu("Ustaw konkretny Hotcue")
        for i in range(8):
            hotcue_menu.addAction(f"Hotcue {i+1}", lambda idx=i: self.controller.set_hotcue(idx))

        menu.addSeparator()
        act_loop_in = menu.addAction("Ustaw Loop In tutaj")
        act_loop_out = menu.addAction("Ustaw Loop Out tutaj")
        act_loop_here = menu.addAction("Ustaw krótki loop tutaj (4 takty)")

        chosen = menu.exec(self.waveform.mapToGlobal(pos))
        if not chosen:
            return

        if chosen == act_cue:
            self.controller.seek(click_ms)
            self.controller.status_changed.emit("CUE SET (waveform menu)")
        elif chosen == act_hotcue_free:
            for idx in range(8):
                if self.controller.get_hotcue(idx) is None:
                    self.controller.set_hotcue(idx, click_ms)
                    return
            self.controller.set_hotcue(0, click_ms)
        elif chosen == act_loop_in:
            self.controller.set_loop_points(click_ms, None)
        elif chosen == act_loop_out:
            if getattr(self.controller, "_loop_in_ms", None) is not None:
                self.controller.set_loop_points(self.controller._loop_in_ms, click_ms)
            else:
                self.controller.status_changed.emit("Najpierw ustaw Loop In")
        elif chosen == act_loop_here:
            bpm = getattr(self.controller, "_original_bpm", None) or getattr(self.controller, "_bpm", None) or 128
            loop_len_ms = int((4 * 60000) / bpm)
            self.controller.set_loop_points(click_ms, click_ms + loop_len_ms)

    # ------------------------------------------------------------------
    # Sygnały z kontrolera → UI
    # ------------------------------------------------------------------
    def _connect_controller_signals(self) -> None:
        c = self.controller
        c.track_loaded.connect(self._on_track_loaded)
        c.track_unloaded.connect(self._on_track_unloaded)
        c.playhead_changed.connect(self._on_playhead_changed)
        c.bpm_changed.connect(self._on_bpm_changed)
        c.hotcue_changed.connect(self._on_hotcue_changed)
        c.play_state_changed.connect(self._on_play_state_changed)
        c.status_changed.connect(self._on_status_changed)
        c.keylock_changed.connect(self.pitch_control.set_keylock)
        c.loop_changed.connect(self._on_loop_changed)
        c.sync_state_changed.connect(self._on_sync_changed)

    def _on_track_loaded(self, track: Track) -> None:
        self._current_track = track
        name = getattr(track, "title", None) or Path(getattr(track, "path", "")).stem or "Nieznany"
        self.title_label.setText(name)

        bpm = getattr(track, "bpm", None)
        self.bpm_label.setText(f"{bpm:.1f}" if bpm and bpm > 10 else "— BPM")

        if WaveformWidget is not None and hasattr(self.waveform, "set_expected_waveform_token"):
            token = str(getattr(track, "path", ""))
            self.waveform.set_expected_waveform_token(token)

        duration = 0
        try:
            if self.controller.playback_engine:
                st = self.controller.playback_engine.get_deck_state(self.controller.deck_id)
                duration = getattr(st, "duration_ms", 0) or 0
        except Exception:
            pass
        self._current_duration_ms = duration

        if WaveformWidget is not None and getattr(track, "path", None):
            self.controller.request_waveform_load(self.waveform, track.path, duration)

        self.hotcue_grid.clear_all()
        self.eq_strip.reset_to_flat()

        self.trim_slider.blockSignals(True)
        self.trim_slider.setValue(85)
        self.trim_slider.blockSignals(False)

        self.time_label.setText("0:00 / " + _format_ms(duration))

    def _on_track_unloaded(self) -> None:
        self.title_label.setText("Brak utworu")
        self.bpm_label.setText("— BPM")
        self.time_label.setText("0:00 / 0:00")
        self._current_duration_ms = 0
        if hasattr(self.waveform, "clear"):
            self.waveform.clear()
        self.hotcue_grid.clear_all()

    def _on_playhead_changed(self, ms: int) -> None:
        self._last_playhead_ms = ms
        if hasattr(self.waveform, "set_playhead"):
            self.waveform.set_playhead(ms)
        pos = _format_ms(ms)
        dur = _format_ms(self._current_duration_ms)
        self.time_label.setText(f"{pos} / {dur}")

    def _on_bpm_changed(self, bpm: float | None) -> None:
        if bpm and bpm > 10:
            self.bpm_label.setText(f"{bpm:.1f}")
        else:
            self.bpm_label.setText("— BPM")

    def _on_hotcue_changed(self, index: int, time_ms: int | None) -> None:
        pad = self.hotcue_grid.get_pad(index)
        if pad:
            if time_ms is not None:
                pad.set_cue_time(time_ms)
            else:
                pad.clear_cue()

    def _on_play_state_changed(self, playing: bool) -> None:
        self.transport.set_playing(playing)

    def _on_status_changed(self, text: str) -> None:
        if hasattr(self, "status_label"):
            self.status_label.setText(text)
            if any(x in text for x in ("MEM", "CUE", "SYNC", "LOOP", "PFL")):
                QtCore.QTimer.singleShot(1300, lambda: self.status_label.setText(f"DECK {self.deck_label}"))

    def _on_loop_changed(self, start_ms: int | None, end_ms: int | None) -> None:
        if hasattr(self.waveform, "set_loop"):
            if start_ms is not None and end_ms is not None:
                self.waveform.set_loop(start_ms, end_ms)
                self.loop_toggle_btn.setChecked(True)
            else:
                if hasattr(self.waveform, "clear_loop"):
                    self.waveform.clear_loop()
                self.loop_toggle_btn.setChecked(False)

    def _on_sync_changed(self, active: bool) -> None:
        self.sync_btn.setChecked(active)
        self.sync_btn.setText("SYNC✓" if active else "SYNC")
        # booth polish: highlight when synced (uses accent from palette via stylesheet if extended)
        if active:
            self.sync_btn.setStyleSheet("background-color: #166534; color: #e0f2e0; font-weight:900;")
        else:
            self.sync_btn.setStyleSheet("")  # revert to default from pro_row

    # ------------------------------------------------------------------
    # Pomocnicze dla DualConsoleWidget
    # ------------------------------------------------------------------
    def set_partner_controller(self, other: DeckController | None) -> None:
        """Podłącz SYNC do drugiego decku."""
        self._partner = other
        # Odłącz stare
        try:
            self.sync_btn.clicked.disconnect()
        except Exception:
            pass
        if other is not None:
            self.sync_btn.clicked.connect(lambda: self.controller.do_sync(other))
        else:
            self.sync_btn.clicked.connect(lambda: self.controller.status_changed.emit("Brak partnera SYNC"))

    def get_waveform_widget(self):
        return self.waveform

    # ------------------------------------------------------------------
    # Drag & drop z library_widget (bezpośrednio na ten deck – pro UX)
    # ------------------------------------------------------------------
    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat("application/x-lumbago-track-paths") or event.mimeData().hasUrls():
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
            try:
                from pathlib import Path as PathLib
                from core.models import Track
                from data.repository import get_track_by_path
                p = paths[0]
                name = PathLib(p).stem
                track = Track(path=p, title=name)
                dbt = get_track_by_path(p)
                if dbt and getattr(dbt, "id", None):
                    track = dbt
                self.controller.load_track(track)
                # optional status
                if hasattr(self, "status_label"):
                    self.status_label.setText("✓ Załadowano via D&D")
            except Exception as exc:
                logger = __import__("logging").getLogger(__name__)
                logger.warning(f"ConsoleDeckView drop error: {exc}")
            event.acceptProposedAction()


__all__ = ["ConsoleDeckView"]
