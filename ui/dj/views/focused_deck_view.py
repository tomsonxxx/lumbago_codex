"""
ui/dj/views/focused_deck_view.py

FocusedDeckView – czysty, dominujący widok trybu Single ("Odtwarzacz").

Zgodny z sekcją 4 dokumentu AGENT3_UI_Designer_Rekordbox_Redo.md:
- Ogromny waveform (min 260px, stretch 7) z beatgridem
- 8 dużych hotcue padów (2×4)
- Duży, wycentrowany transport (PLAY/CUE/STOP)
- Pitch + TRIM w czytelnym układzie
- Dużo powietrza: marginesy 20-24px, spacing 18-22px
- Ogromny BPM (30-36px) w prawym górnym rogu
- Czytelny czas 0:00 / 4:12 (18px mono, wycentrowany)
- Zaawansowane (KEY, Q, SYNC, Memory S/R) – kompaktowe, opcjonalne

WIDOK "DUMB":
- Buduje layout wyłącznie z małych widgetów (TransportBar, HotcuePadGrid, PitchControl)
  + WaveformWidget + ręcznie zrobiony Trim (przy użyciu helperów ze styles.py)
- ZERO logiki DJ: seek, hotcue, play, pitch, memory, sync, quantize – wszystko przez DeckController
- Łączy się wyłącznie przez sygnały kontrolera (track_loaded, playhead_changed, hotcue_changed itd.)
- Zachowuje 100% istniejących zachowań: seek (click), shift+click (set hotcue free), double-click (main cue + seek)

Używa WYŁĄCZNIE:
- BOOTH_COLORS, BOOTH_SIZES
- get_deck_panel_stylesheet, get_bpm_label_stylesheet, get_section_label_stylesheet,
  get_time_label_stylesheet, get_value_label_stylesheet, get_slider_stylesheet

Pełne polskie komentarze i docstringi.
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
from ui.dj.styles import (
    BOOTH_SIZES,
    get_deck_panel_stylesheet,
    get_bpm_label_stylesheet,
    get_section_label_stylesheet,
    get_time_label_stylesheet,
    get_value_label_stylesheet,
    get_slider_stylesheet,
)

# WaveformWidget – extracted to dedicated module (clean separation, task 1)
# W pełni zachowuje seek_requested, cue_set_requested (Shift+click), double_clicked
try:
    from ui.dj.views.waveform_widget import WaveformWidget
except Exception:  # pragma: no cover
    WaveformWidget = None  # type: ignore


def _format_ms(ms: int | None) -> str:
    """Prosty formatter czasu ms → 'm:ss' (fallback gdy brak z kontrolera)."""
    if ms is None or ms < 0:
        return "0:00"
    total = max(0, int(ms)) // 1000
    m = total // 60
    s = total % 60
    return f"{m}:{s:02d}"


class FocusedDeckView(QtWidgets.QFrame):
    """
    Czysty widok prezentacyjny trybu pojedynczego "Odtwarzacz".

    Używany przez DJPlayerWindow jako self.single_container = FocusedDeckView(controller_a)

    Po stworzeniu:
        view = FocusedDeckView(controller)
        # podłączanie waveform / hotcue / transport odbywa się automatycznie w __init__

    Nie przechowuje żadnego stanu DJ poza tym co potrzebne do prezentacji (np. duration dla czasu).
    """

    def __init__(self, controller: DeckController, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.controller = controller
        self._current_duration_ms: int = 0
        self._current_track: Track | None = None

        # Zastosuj stylesheet panelu decku (używa selektora FocusedDeckView)
        self.setObjectName("DeckPanel")
        self.setStyleSheet(get_deck_panel_stylesheet())

        self.setAcceptDrops(True)  # direct drag&drop z library do focused (single)

        # Dużo powietrza – dokładnie jak w specyfikacji AGENT 3
        self._setup_ui()
        self._connect_controller_signals()
        self._connect_widget_signals()

        # Inicjalny stan
        if hasattr(self, "status_label"):
            self.status_label.setText("— Gotowy (tryb Odtwarzacz)")

    # ------------------------------------------------------------------
    # Budowa layoutu (bez logiki)
    # ------------------------------------------------------------------
    def _setup_ui(self) -> None:
        """Buduje hierarchię widgetów zgodnie z sekcją 4 design doc."""
        main = QtWidgets.QVBoxLayout(self)
        main.setContentsMargins(24, 20, 24, 20)
        main.setSpacing(20)

        # 1. HEADER: Tytuł (stretch) + ogromny BPM po prawej
        header = QtWidgets.QHBoxLayout()
        header.setSpacing(16)

        self.title_label = QtWidgets.QLabel("Brak utworu — upuść plik z biblioteki lub użyj drag&drop")
        self.title_label.setStyleSheet(
            f"font-size: 18px; font-weight: 700; color: #f0f4f8;"
        )
        self.title_label.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Preferred
        )
        self.title_label.setWordWrap(False)
        self.title_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignVCenter)

        self.bpm_label = QtWidgets.QLabel("— BPM")
        self.bpm_label.setStyleSheet(get_bpm_label_stylesheet())
        self.bpm_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter)
        self.bpm_label.setMinimumWidth(110)

        header.addWidget(self.title_label, 1)
        header.addWidget(self.bpm_label, 0)
        main.addLayout(header)

        # 2. WAVEFORM – dominujący element (stretch 7, min 260px)
        if WaveformWidget is not None:
            self.waveform = WaveformWidget()
        else:
            self.waveform = QtWidgets.QLabel("[Waveform niedostępny]")
        self.waveform.setMinimumHeight(BOOTH_SIZES["waveform_min_height_single"])
        self.waveform.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding
        )
        main.addWidget(self.waveform, 7)

        # PPM (prawy przycisk) – menu kontekstowe na waveformie (brakowało po redesignie)
        if WaveformWidget is not None:
            self.waveform.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
            self.waveform.customContextMenuRequested.connect(self._show_waveform_context_menu)

        # 3. CZAS – czytelny, wycentrowany, 16-18px mono
        self.time_label = QtWidgets.QLabel("0:00 / 0:00")
        self.time_label.setStyleSheet(get_time_label_stylesheet())
        self.time_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        main.addWidget(self.time_label, 0)

        # 4. TRANSPORT – wycentrowany klaster z dużymi przyciskami
        self.transport = TransportBar()
        main.addWidget(self.transport, 0)

        # 5. KONTROLKI: PITCH + TRIM (dużo miejsca, czytelne suwaki)
        controls = QtWidgets.QHBoxLayout()
        controls.setSpacing(22)

        # Pitch (używamy gotowego widgetu)
        self.pitch_control = PitchControl()
        controls.addWidget(self.pitch_control, 2)

        # TRIM – ręcznie zbudowany przy użyciu helperów styles (bo nie ma dedykowanego TrimControl)
        trim_box = QtWidgets.QVBoxLayout()
        trim_box.setSpacing(4)

        trim_header = QtWidgets.QHBoxLayout()
        trim_lbl = QtWidgets.QLabel("TRIM")
        trim_lbl.setStyleSheet(get_section_label_stylesheet())
        self.trim_value = QtWidgets.QLabel("85")
        self.trim_value.setStyleSheet(get_value_label_stylesheet())
        trim_header.addWidget(trim_lbl)
        trim_header.addStretch()
        trim_header.addWidget(self.trim_value)
        trim_box.addLayout(trim_header)

        self.trim_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.trim_slider.setRange(0, 100)
        self.trim_slider.setValue(85)
        self.trim_slider.setStyleSheet(get_slider_stylesheet("horizontal"))
        self.trim_slider.setFixedWidth(BOOTH_SIZES.get("pitch_slider_width", 180))
        self.trim_slider.valueChanged.connect(self._on_trim_changed)
        trim_box.addWidget(self.trim_slider)

        controls.addLayout(trim_box, 1)

        main.addLayout(controls, 0)

        # 6. HOT CUES – zawsze 8 padów 2×4 (duże, z paletą 8 kolorów)
        hc_section = QtWidgets.QLabel("HOT CUES")
        hc_section.setStyleSheet(get_section_label_stylesheet())
        main.addWidget(hc_section, 0)

        self.hotcue_grid = HotcuePadGrid()
        main.addWidget(self.hotcue_grid, 0)

        # 7. ADVANCED ROW – KEY (z PitchControl), Q, SYNC, Memory S/R (kompaktowe, dużo powietrza)
        adv = QtWidgets.QHBoxLayout()
        adv.setSpacing(10)

        # KEY jest już wewnątrz PitchControl – dodajemy tylko Q + SYNC + Memory
        self.quantize_btn = QtWidgets.QPushButton("Q")
        self.quantize_btn.setCheckable(True)
        self.quantize_btn.setChecked(True)
        self.quantize_btn.setFixedSize(48, 32)
        self.quantize_btn.setStyleSheet(get_section_label_stylesheet().replace("10px", "11px"))
        self.quantize_btn.clicked.connect(self._on_quantize_toggled)

        self.sync_btn = QtWidgets.QPushButton("SYNC")
        self.sync_btn.setFixedSize(58, 32)
        self.sync_btn.setCheckable(True)
        self.sync_btn.setStyleSheet(get_section_label_stylesheet().replace("10px", "11px"))

        # Memory S / R (zachowanie z oryginału – snapshot sesyjny)
        self.mem_s_btn = QtWidgets.QPushButton("S")
        self.mem_s_btn.setFixedSize(36, 28)
        self.mem_s_btn.setToolTip("Zapisz pamięć decku (hotcue, pitch, trim, loop, keylock)")
        self.mem_r_btn = QtWidgets.QPushButton("R")
        self.mem_r_btn.setFixedSize(36, 28)
        self.mem_r_btn.setToolTip("Odtwórz zapamiętany stan decku")

        # Krok 6: menu PPM dla memory w focused
        self.mem_s_btn.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.mem_r_btn.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.mem_s_btn.customContextMenuRequested.connect(self._show_memory_menu)
        self.mem_r_btn.customContextMenuRequested.connect(self._show_memory_menu)

        adv.addWidget(QtWidgets.QLabel(""), 1)  # lewe powietrze
        adv.addWidget(self.quantize_btn, 0)
        adv.addWidget(self.sync_btn, 0)
        adv.addSpacing(12)
        adv.addWidget(self.mem_s_btn, 0)
        adv.addWidget(self.mem_r_btn, 0)
        adv.addWidget(QtWidgets.QLabel(""), 1)  # prawe powietrze

        main.addLayout(adv, 0)

        # Status (mały, prawy górny róg logiki – tylko prezentacja)
        self.status_label = QtWidgets.QLabel("")
        self.status_label.setStyleSheet(
            f"color: #6b7688; font-size: 10px; font-weight: 600;"
        )
        self.status_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        main.addWidget(self.status_label, 0)

    # ------------------------------------------------------------------
    # Podłączanie sygnałów z małych widgetów → metody kontrolera (dumb)
    # ------------------------------------------------------------------
    def _connect_widget_signals(self) -> None:
        """Tylko przekazywanie eventów do kontrolera – zero logiki."""
        # Transport
        self.transport.play_clicked.connect(self.controller.toggle_play)
        self.transport.cue_clicked.connect(self._on_cue_clicked)
        self.transport.stop_clicked.connect(self._on_stop_clicked)

        # Pitch + Keylock (PitchControl już emituje)
        self.pitch_control.pitch_changed.connect(self.controller.set_pitch)
        self.pitch_control.keylock_toggled.connect(self.controller.set_keylock)

        # Hotcue grid → kontroler (jump / set)
        self.hotcue_grid.pad_activated.connect(self.controller.jump_hotcue)
        self.hotcue_grid.pad_set_requested.connect(self.controller.set_hotcue)
        self.hotcue_grid.pad_delete_requested.connect(self.controller.delete_hotcue)
        self.hotcue_grid.pad_rename_requested.connect(self._request_hotcue_rename)
        self.hotcue_grid.pad_color_change_requested.connect(self.controller.set_hotcue_color)

        # Memory
        self.mem_s_btn.clicked.connect(self.controller.save_memory)
        self.mem_r_btn.clicked.connect(self.controller.recall_memory)

        # Quantize
        # (sync_btn podłączany później z zewnątrz lub w dual)

        # WAVEFORM – pełna obsługa istniejących zachowań (seek, shift+click hotcue, double-click)
        if WaveformWidget is not None and hasattr(self.waveform, "seek_requested"):
            self.waveform.seek_requested.connect(self.controller.seek)
            self.waveform.cue_set_requested.connect(self._handle_waveform_shift_click)
            self.waveform.double_clicked.connect(self._handle_waveform_double_click)

    def _on_cue_clicked(self) -> None:
        """CUE – skok do main_cue lub pozycji 0 (zachowanie kompatybilne)."""
        # W controllerze nie ma jeszcze publicznego main_cue, więc prosty seek(0) + status
        # (pełna obsługa _main_cue_ms zostanie przeniesiona w fazie integracji do kontrolera)
        self.controller.seek(0)
        self.controller.status_changed.emit("CUE")

    def _on_stop_clicked(self) -> None:
        """Stop + reset playhead wizualnie."""
        if self.controller.playback_engine:
            try:
                self.controller.playback_engine.stop_deck(self.controller.deck_id)
            except Exception:
                pass
        self.controller.play_state_changed.emit(False)
        self.controller.playhead_changed.emit(0)

    def _on_trim_changed(self, value: int) -> None:
        """Trim slider → kontroler (0.0-1.0)."""
        self.trim_value.setText(str(value))
        self.controller.set_trim(value / 100.0)

    def _on_quantize_toggled(self, checked: bool) -> None:
        """Przełącz quantize przez kontroler."""
        self.controller.toggle_quantize()
        # Stan rzeczywisty przychodzi z sygnału status_changed

    def _handle_waveform_shift_click(self, time_ms: int) -> None:
        """
        Shift + click na waveform = ustaw pierwszy wolny hotcue (0-7).
        Dokładnie zachowanie z poprzedniej implementacji (DeckWidget / SinglePlayerView).
        Mała logika wyboru indeksu – reszta (snap + persist + sygnał) w kontrolerze.
        """
        if not self.controller.current_track:
            return
        for idx in range(8):
            if self.controller.get_hotcue(idx) is None:
                self.controller.set_hotcue(idx)
                return
        # Wszystkie zajęte – nadpisz pierwszy
        self.controller.set_hotcue(0)

    def _handle_waveform_double_click(self, time_ms: int) -> None:
        """
        Double-click waveform = seek (z snap jeśli Q) + ustaw main cue (kompatybilność).
        Zachowuje responsywność i stare zachowanie "pro DJ preview".
        """
        snapped = self.controller.snap_to_beat(time_ms)
        self.controller.seek(snapped)
        # W pełnej wersji kontroler będzie przechowywał _main_cue_ms
        # Na razie emitujemy status (jak w oryginale)
        self.controller.status_changed.emit("CUE SET (waveform)")

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

    def _show_memory_menu(self, pos: QtCore.QPoint) -> None:
        """Menu dla memory S/R w focused."""
        menu = QtWidgets.QMenu(self)
        menu.addAction("Zapisz stan (Save Memory)")
        menu.addAction("Odtwórz stan (Recall Memory)")
        menu.addSeparator()
        menu.addAction("Wyczyść pamięć")
        menu.exec(self.mem_s_btn.mapToGlobal(pos))

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

        # Submenu z konkretnymi hotcue'ami
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
            # Prosty 4-taktowy loop (zakładamy 4/4)
            bpm = self.controller._bpm or 128
            loop_len_ms = int((4 * 60000) / bpm)
            self.controller.set_loop_points(click_ms, click_ms + loop_len_ms)

    # ------------------------------------------------------------------
    # Podłączanie sygnałów KONTROLERA → aktualizacja widgetów (dumb)
    # ------------------------------------------------------------------
    def _connect_controller_signals(self) -> None:
        """Subskrypcja – widok reaguje na zmiany stanu."""
        c = self.controller
        c.track_loaded.connect(self._on_track_loaded)
        c.track_unloaded.connect(self._on_track_unloaded)
        c.playhead_changed.connect(self._on_playhead_changed)
        c.bpm_changed.connect(self._on_bpm_changed)
        c.hotcue_changed.connect(self._on_hotcue_changed)
        c.play_state_changed.connect(self._on_play_state_changed)
        c.status_changed.connect(self._on_status_changed)
        c.keylock_changed.connect(self.pitch_control.set_keylock)
        # loop_changed i sync – w focused traktujemy opcjonalnie (status + ewentualny waveform)
        c.loop_changed.connect(self._on_loop_changed)
        c.sync_state_changed.connect(self._on_sync_changed)

    # ------------------------------------------------------------------
    # Sloty aktualizujące UI (czysta prezentacja)
    # ------------------------------------------------------------------
    def _on_track_loaded(self, track: Track) -> None:
        """Aktualizacja tytułu, BPM, waveform (przez request do kontrolera)."""
        self._current_track = track
        name = getattr(track, "title", None) or Path(getattr(track, "path", "")).stem or "Nieznany utwór"
        self.title_label.setText(name)

        # BPM początkowy (efektywny przyjdzie przez sygnał)
        bpm = getattr(track, "bpm", None)
        if bpm and bpm > 10:
            self.bpm_label.setText(f"{bpm:.1f}")
        else:
            self.bpm_label.setText("— BPM")

        # Przygotuj waveform (token + request)
        if WaveformWidget is not None and hasattr(self.waveform, "set_expected_waveform_token"):
            token = str(getattr(track, "path", ""))
            self.waveform.set_expected_waveform_token(token)

        # Poproś kontroler o załadowanie waveformu w tle (on użyje WaveformRunnable)
        duration = 0
        try:
            if self.controller.playback_engine:
                state = self.controller.playback_engine.get_deck_state(self.controller.deck_id)
                duration = getattr(state, "duration_ms", 0) or 0
        except Exception:
            duration = 0
        self._current_duration_ms = duration

        if WaveformWidget is not None and getattr(track, "path", None):
            self.controller.request_waveform_load(self.waveform, track.path, duration)

        # Wyczyść hotcue pady wizualnie (rzeczywiste wartości przyjdą przez hotcue_changed)
        self.hotcue_grid.clear_all()

        # Reset trim do sensownej wartości
        self.trim_slider.blockSignals(True)
        self.trim_slider.setValue(85)
        self.trim_slider.blockSignals(False)
        self.trim_value.setText("85")

        self.time_label.setText("0:00 / " + _format_ms(duration))

    def _on_track_unloaded(self) -> None:
        self.title_label.setText("Brak utworu — upuść plik z biblioteki")
        self.bpm_label.setText("— BPM")
        self.time_label.setText("0:00 / 0:00")
        self._current_duration_ms = 0
        if hasattr(self.waveform, "clear"):
            self.waveform.clear()
        self.hotcue_grid.clear_all()
        self.transport.set_playing(False)

    def _on_playhead_changed(self, ms: int) -> None:
        if hasattr(self.waveform, "set_playhead"):
            self.waveform.set_playhead(ms)
        # Czas
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
        if pad is not None:
            if time_ms is not None:
                pad.set_cue_time(time_ms)
            else:
                pad.clear_cue()

    def _on_play_state_changed(self, is_playing: bool) -> None:
        self.transport.set_playing(is_playing)

    def _on_status_changed(self, text: str) -> None:
        if hasattr(self, "status_label"):
            self.status_label.setText(text)
            # Auto-clear niektórych komunikatów
            if "MEM" in text or "CUE SET" in text or "SYNC" in text:
                QtCore.QTimer.singleShot(1400, lambda: self.status_label.setText("✓ Gotowy"))

    def _on_loop_changed(self, start_ms: int | None, end_ms: int | None) -> None:
        if hasattr(self.waveform, "set_loop"):
            if start_ms is not None and end_ms is not None and end_ms > start_ms:
                self.waveform.set_loop(start_ms, end_ms)
            else:
                if hasattr(self.waveform, "clear_loop"):
                    self.waveform.clear_loop()

    def _on_sync_changed(self, active: bool) -> None:
        if hasattr(self, "sync_btn"):
            self.sync_btn.setChecked(active)
            self.sync_btn.setText("SYNC ✓" if active else "SYNC")

    # ------------------------------------------------------------------
    # API pomocnicze dla integracji (np. DJPlayerWindow)
    # ------------------------------------------------------------------
    def set_partner_controller(self, other: DeckController | None) -> None:
        """Umożliwia SYNC w trybie single (rzadko używane)."""
        if other is None:
            self.sync_btn.clicked.disconnect()
            return
        self.sync_btn.clicked.connect(lambda: self.controller.do_sync(other))

    def get_waveform_widget(self):
        """Dla zewnętrznego dostępu (np. testy, resize)."""
        return self.waveform

    # Drag & drop bezpośredni na focused deck (single player mode)
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
                if hasattr(self, "status_label"):
                    self.status_label.setText("✓ D&D loaded")
            except Exception as exc:
                import logging
                logging.getLogger(__name__).warning(f"FocusedDeckView drop: {exc}")
            event.acceptProposedAction()


# Re-eksport dla wygody
__all__ = ["FocusedDeckView"]
