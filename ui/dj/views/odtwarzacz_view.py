from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from PyQt6 import QtCore, QtGui, QtWidgets

from core.models import Track
from ui.dj.simple_deck_controller import SimpleDeckController
from ui.dj.views.waveform_widget import WaveformWidget
from ui.dj.styles import (
    BOOTH_COLORS,
    BOOTH_SIZES,
    get_deck_panel_stylesheet,
    get_bpm_label_stylesheet,
    get_time_label_stylesheet,
    get_transport_button_stylesheet,
)

logger = logging.getLogger(__name__)


def _format_ms(ms: int | None) -> str:
    """Prosty formatter ms → m:ss (dla czasu i statusu)."""
    if ms is None or ms < 0:
        return "0:00"
    total = max(0, int(ms)) // 1000
    m = total // 60
    s = total % 60
    return f"{m}:{s:02d}"


class OdtwarzaczView(QtWidgets.QFrame):
    """
    Minimalny widok single player "Odtwarzacz" MVP (QFrame).

    Skupiony TYLKO na podstawach (per zadanie):
    - poprawne ładowanie pliku (z lookup repo w drop + load)
    - podstawowy playback: play/pause/stop (via SimpleDeckController)
    - wizualizacje: title/time/BPM/duży waveform+playhead+beatgrid
    - czysty layout z powietrzem (VBox + marginesy/stretch)

    Hierarchia layoutu (VBox, margins ~32/24, spacing 18):
    - Header HBox: [TRACK TITLE 18px bold stretch]          [BPM 32px 900 accent]
    - WAVEFORM (min 260, stretch=7) z BPM-aware beatgrid + gruby playhead
    - TIME (18px mono, center, stretch=0)
    - TRANSPORT (3 duże przyciski CUE/PLAY/STOP wycentrowane z side stretches)
    - minimal status (11px muted, center)

    Używa:
    - ui/dj/styles (BOOTH_COLORS, BOOTH_SIZES, get_*_stylesheet, get_transport_button_stylesheet)
    - WaveformWidget (nowy extracted)
    - Transport styles (ale własne 3 przyciski dla prostoty MVP + explicit play/pause)
    - ZERO: hotcues, pitch, trim, eq, mem, advanced row, loops, sync

    Drag&drop: pełny repo lookup (get_track_by_path).
    Connects: waveform seek + buttons to controller; subs signals for UI updates.

    Nie miesza z FocusedDeckView (pozostaje dla dual console).
    """
    def __init__(self, controller: SimpleDeckController,
                 parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.controller = controller
        self._current_duration_ms: int = 0
        self._current_track: Track | None = None
        self._is_playing: bool = False

        self.setObjectName("OdtwarzaczPanel")
        self.setStyleSheet(get_deck_panel_stylesheet())

        self.setAcceptDrops(True)

        self._setup_ui()
        self._connect_controller_signals()
        self._connect_widget_signals()

    def _setup_ui(self) -> None:
        """VBox z powietrzem + hierarchia z designu (dostosowana do MVP basics)."""
        layout = QtWidgets.QVBoxLayout(self)
        # Dużo powietrza: 32px boki, 24 góra/dół, spacing 18 (per spec + "32px etc")
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(18)

        # === HEADER: title + BPM (HBox, spacing 16) ===
        header = QtWidgets.QHBoxLayout()
        header.setSpacing(16)

        self.title_label = QtWidgets.QLabel(
            "Brak utworu — upuść plik z biblioteki")
        self.title_label.setStyleSheet(
            "font-size: 18px; font-weight: 700; "
            f"color: {BOOTH_COLORS['text_primary']};")
        self.title_label.setWordWrap(False)
        self.title_label.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Preferred
        )
        header.addWidget(self.title_label, 1)

        self.bpm_label = QtWidgets.QLabel("— BPM")
        self.bpm_label.setStyleSheet(get_bpm_label_stylesheet())
        self.bpm_label.setAlignment(
            QtCore.Qt.AlignmentFlag.AlignRight
            | QtCore.Qt.AlignmentFlag.AlignVCenter)
        self.bpm_label.setMinimumWidth(100)
        header.addWidget(self.bpm_label, 0)

        layout.addLayout(header)

        # === DOMINANT WAVEFORM (stretch 7, minHeight 260+) ===
        self.waveform = WaveformWidget()
        min_h = BOOTH_SIZES.get("waveform_min_height_single", 260)
        self.waveform.setMinimumHeight(min_h)
        self.waveform.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding
        )
        layout.addWidget(self.waveform, 7)

        # === TIME (center, fixed, 0 stretch, 18px mono) ===
        self.time_label = QtWidgets.QLabel("0:00 / 0:00")
        self.time_label.setStyleSheet(get_time_label_stylesheet())
        self.time_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.time_label, 0)

        # === LARGE CENTERED TRANSPORT (3 buttons, reuse transport styles + sizes) ===
        trans = QtWidgets.QHBoxLayout()
        trans.setSpacing(14)
        trans.addStretch(1)

        # CUE (dla set_cue w MVP)
        cue_size = BOOTH_SIZES.get("transport_cue", (78, 52))
        self.cue_btn = QtWidgets.QPushButton("CUE")
        self.cue_btn.setFixedSize(*cue_size)
        self.cue_btn.setStyleSheet(get_transport_button_stylesheet("cue"))
        self.cue_btn.clicked.connect(self.controller.set_cue)
        self.cue_btn.setToolTip("Ustaw punkt CUE na bieżącej pozycji (lub skocz do istniejącego). EFEKT: następny PLAY zacznie odtwarzanie od tego punktu cue w załadowanym pliku audio (nie zmienia pliku).")

        # PLAY / toggle (duży)
        play_size = BOOTH_SIZES.get("transport_play", (96, 58))
        self.play_btn = QtWidgets.QPushButton("▶  ODTWÓRZ")
        self.play_btn.setFixedSize(*play_size)
        self.play_btn.setStyleSheet(get_transport_button_stylesheet("play"))
        self.play_btn.clicked.connect(self._on_play_or_pause_clicked)
        self.play_btn.setToolTip("Rozpocznij lub wznów odtwarzanie załadowanego pliku audio. EFEKT: uruchamia silnik playback na fizycznym pliku (od pozycji lub cue jeśli blisko startu). Kliknij ponownie by pauzować.")

        # STOP
        stop_size = BOOTH_SIZES.get("transport_stop", (68, 52))
        self.stop_btn = QtWidgets.QPushButton("■  STOP")
        self.stop_btn.setFixedSize(*stop_size)
        self.stop_btn.setStyleSheet(get_transport_button_stylesheet("stop"))
        self.stop_btn.clicked.connect(self.controller.stop)
        self.stop_btn.setToolTip("Zatrzymaj odtwarzanie i wróć do punktu CUE (lub 0). EFEKT: stop silnika + reset playhead do cue w załadowanym pliku (nie usuwa pliku z decku).")

        trans.addWidget(self.cue_btn)
        trans.addWidget(self.play_btn)
        trans.addWidget(self.stop_btn)
        trans.addStretch(1)

        layout.addLayout(trans)

        # === MINIMAL STATUS ===
        self.status_label = QtWidgets.QLabel("— Gotowy (tryb Odtwarzacz MVP)")
        self.status_label.setStyleSheet(
            f"color: {BOOTH_COLORS.get('text_muted', '#6b7688')}; font-size: 11px;"
        )
        self.status_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label, 0)

        # Oddychanie na dole
        layout.addStretch(1)

    def _connect_widget_signals(self) -> None:
        """Waveform seek (bez cue/double w minimal – double działa jako seek + set_cue)."""
        if hasattr(self.waveform, "seek_requested"):
            self.waveform.seek_requested.connect(self.controller.seek)
        if hasattr(self.waveform, "double_clicked"):
            # Double = seek + set as cue (pro preview + basic cue logic)
            self.waveform.double_clicked.connect(
                lambda t: (self.controller.seek(t), self.controller.set_cue())
            )
        # Shift+click na waveform ignorujemy w MVP (no hotcues)

    def _connect_controller_signals(self) -> None:
        """Subskrypcja tylko podstawowych sygnałów kontrolera."""
        self.controller.track_loaded.connect(self._on_track_loaded)
        self.controller.track_unloaded.connect(self._on_track_unloaded)
        self.controller.playhead_changed.connect(self._on_playhead_changed)
        self.controller.bpm_changed.connect(self._on_bpm_changed)
        self.controller.play_state_changed.connect(self._on_play_state_changed)
        self.controller.status_changed.connect(self._on_status_changed)

    # ------------------------------------------------------------------
    # UI update slots (dumb view)
    # ------------------------------------------------------------------
    def _on_track_loaded(self, track: Track) -> None:
        self._current_track = track

        pth = getattr(track, "path", None)
        title = getattr(track, "title", None) or (Path(pth).stem if pth else "Utwór")
        artist = getattr(track, "artist", None) or ""
        full = f"{artist} – {title}" if artist else title
        self.title_label.setText(full)

        bpm = getattr(track, "bpm", None)
        if bpm and bpm > 10:
            self.bpm_label.setText(f"{bpm:.1f}")
        else:
            self.bpm_label.setText("— BPM")

        # Przygotuj waveform token (anty-stale)
        pth = getattr(track, "path", None)
        if pth and hasattr(self.waveform, "set_expected_waveform_token"):
            self.waveform.set_expected_waveform_token(str(pth))

        # Duration z engine state (lepsze niż z modelu)
        duration = getattr(track, "duration_ms", 0) or 0
        try:
            if self.controller.playback_engine:
                state = self.controller.playback_engine.get_deck_state(self.controller.deck_id)
                if state and getattr(state, "duration_ms", 0):
                    duration = state.duration_ms
        except Exception:
            pass
        self._current_duration_ms = duration

        self.time_label.setText(f"0:00 / {_format_ms(duration)}")

        # BPM na waveform dla beatgrid (jeśli dostępne)
        if hasattr(self.waveform, "set_bpm"):
            self.waveform.set_bpm(bpm)

        # Poproś kontroler o waveform (view odpowiedzialny, jak w focused)
        if pth and hasattr(self.waveform, "set_expected_waveform_token"):
            self.controller.request_waveform_load(self.waveform, pth, duration)

        self.status_label.setText("✓ Załadowano")

    def _on_track_unloaded(self) -> None:
        self._current_track = None
        self._current_duration_ms = 0
        self._is_playing = False

        self.title_label.setText("Brak utworu — upuść plik z biblioteki")
        self.bpm_label.setText("— BPM")
        self.time_label.setText("0:00 / 0:00")
        if hasattr(self.waveform, "clear"):
            self.waveform.clear()
        if hasattr(self, "play_btn"):
            self.play_btn.setText("▶  ODTWÓRZ")

        self.status_label.setText("— Gotowy (tryb Odtwarzacz MVP)")

    def _on_playhead_changed(self, ms: int) -> None:
        if hasattr(self.waveform, "set_playhead"):
            self.waveform.set_playhead(ms)
        self.time_label.setText(f"{_format_ms(ms)} / {_format_ms(self._current_duration_ms)}")

    def _on_bpm_changed(self, bpm: float | None) -> None:
        if bpm and bpm > 10:
            self.bpm_label.setText(f"{float(bpm):.1f}")
            if hasattr(self.waveform, "set_bpm"):
                self.waveform.set_bpm(bpm)
        # nie nadpisujemy "— BPM" jeśli None (zachowaj z load)

    def _on_play_state_changed(self, playing: bool) -> None:
        self._is_playing = bool(playing)
        if hasattr(self, "play_btn"):
            self.play_btn.setText("❚❚  PAUZA" if playing else "▶  ODTWÓRZ")

    def _on_status_changed(self, text: str) -> None:
        self.status_label.setText(text)

    # ------------------------------------------------------------------
    # Transport MVP (explicit play vs pause, nie toggle w kontrolerze)
    # ------------------------------------------------------------------
    def _on_play_or_pause_clicked(self) -> None:
        if getattr(self, "_is_playing", False):
            self.controller.pause()
        else:
            self.controller.play()

    # ------------------------------------------------------------------
    # Drag & drop z pełnym repo lookup (identycznie jak w main window / _load_dropped_track)
    # ------------------------------------------------------------------
    def dragEnterEvent(self, event: QtGui.QDragEnterEvent) -> None:
        mime = event.mimeData()
        if mime.hasFormat("application/x-lumbago-track-paths") or mime.hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QtGui.QDropEvent) -> None:
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
            self._load_dropped_track(paths[0])
        event.acceptProposedAction()

    def _load_dropped_track(self, path: str) -> None:
        """Pełny lookup z repo jak w dj_player_window._load_dropped_track."""
        try:
            name = Path(path).stem
            track = Track(path=path, title=name)
            # Enrich z DB (id dla przyszłych, tu dla spójności + metadane)
            try:
                from data.repository import get_track_by_path
                dbt = get_track_by_path(path)
                if dbt and getattr(dbt, "id", None):
                    track = dbt
            except Exception as exc:
                logger.debug(f"OdtwarzaczView drop DB lookup: {exc}")
            self.controller.load_track(track)
        except Exception as e:
            msg = "Błąd ładowania upuszczonego tracka w OdtwarzaczView"
            logger.warning(f"{msg}: {e}")
