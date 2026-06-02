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


class _CompactSpinIndicator(QtWidgets.QWidget):
    """
    Pilot-like animated play indicator (spinning CD/vinyl/eq style).
    Używa timer + paintEvent dla rotacji (per SZPIEG: anim via timer/paint).
    Reacts to play_state: start() / stop() spin.
    W compact mode pokazywany obok tytułu lub w transporcie.
    Lekki, skalowalny, nie wymaga external assets.
    """
    def __init__(self, parent=None, size: int = 22):
        super().__init__(parent)
        self._size = size
        self.setFixedSize(size, size)
        self._angle = 0.0
        self._spinning = False
        self._timer = QtCore.QTimer(self)
        self._timer.setInterval(50)  # ~20fps smooth
        self._timer.timeout.connect(self._tick)
        self.setToolTip("Wskaźnik odtwarzania (spinning CD-like). Aktywny podczas PLAY (stream).")

    def start(self):
        if not self._spinning:
            self._spinning = True
            self._timer.start()
            self.update()

    def stop(self):
        if self._spinning:
            self._spinning = False
            self._timer.stop()
            self._angle = 0.0
            self.update()

    def _tick(self):
        self._angle = (self._angle + 12) % 360  # deg per tick, clockwise like vinyl
        self.update()

    def paintEvent(self, event):
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, True)
        w, h = self.width(), self.height()
        cx, cy = w / 2, h / 2
        r = min(w, h) / 2 - 2
        c = BOOTH_COLORS
        # Vinyl/CD like: dark circle + grooves + highlight
        p.setPen(QtGui.QPen(QtGui.QColor(c.get("border_strong", "#3a4556")), 2))
        p.setBrush(QtGui.QBrush(QtGui.QColor(c.get("surface_elev", "#1a212c"))))
        p.drawEllipse(cx - r, cy - r, 2*r, 2*r)
        # Spinning lines (eq bars or spokes)
        p.setPen(QtGui.QPen(QtGui.QColor(c.get("accent", "#00e0ff")), 1.5))
        for i in range(6):
            a = (self._angle + i * 60) * 3.14159 / 180.0
            x1 = cx + r * 0.3 * (1 if i % 2 == 0 else 0.6)
            y1 = cy + r * 0.3 * (1 if i % 2 == 0 else 0.6)
            x2 = cx + r * 0.85 * (1 if i % 2 == 0 else 0.7)
            y2 = cy + r * 0.85 * (1 if i % 2 == 0 else 0.7)
            p.drawLine(int(cx + (x1-cx)*0.6), int(cy + (y1-cy)*0.6), int(cx + (x2-cx)*0.6), int(cy + (y2-cy)*0.6))
        # Center dot
        p.setBrush(QtGui.QBrush(QtGui.QColor(c.get("play", "#22c55e"))))
        p.drawEllipse(cx-2, cy-2, 4, 4)
        p.end()


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

    **Uwaga dla nowych agentów/programistów:** Implementacja dokładnie per nadrzędny SZPIEG Build Spec + Plan team review (z crew/SZPIEG_agent_spec_and_archive.md + memory.md). Patrz docs dla zasad dokumentacji (zawsze update memory/HISTORY/crew/SZPIEG + code docs + todo + commit). SZPIEG spec jest binding — zero odstępstw.

    Skupiony TYLKO na podstawach (per zadanie):
    - poprawne ładowanie pliku (z lookup repo w drop + load)
    - podstawowy playback: play/pause/stop (via SimpleDeckController)
    - wizualizacje: title/time/BPM/duży waveform+playhead+beatgrid
    - czysty layout z powietrzem (VBox + marginesy/stretch)
    - compact pilot mode z animacją (spinning indicator), EFFECT tooltips, scalability, drag, file vs stream clarity.

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
        self._compact: bool = False

        self.setObjectName("OdtwarzaczPanel")
        self._normal_stylesheet = get_deck_panel_stylesheet()
        self.setStyleSheet(self._normal_stylesheet)

        self.setAcceptDrops(True)

        self._setup_ui()
        self._connect_controller_signals()
        self._connect_widget_signals()

        # Initial apply (default non-compact uses normal sizes)
        self._apply_compact_ui()

        # Overall EFFECT tooltip for the odt panel (air + drag + file/stream clarity)
        self.setToolTip(
            "Odtwarzacz (single preview): czysty, skalowalny widok z powietrzem. "
            "Drag z tabeli biblioteki = load PLIKU (mime + repo lookup + highlight safety). "
            "Transport = STREAM playback z pliku (play near cue, stop->cue). "
            "Compact toggle w oknie rodzica. ResizeEvent dla skalowalności. "
            "EFEKT: nie zachodzi na dual, nie nadpisuje metadanych."
        )

    def _setup_ui(self) -> None:
        """VBox z powietrzem + hierarchia z designu (dostosowana do MVP basics).
        FILE vs STREAM: wszystkie load_* = operacje na PLIKU (ścieżka dysku + DB lookup + waveform peaks).
        Transport (play/pause/stop/seek) = operacje na STREAMIE (dźwięk z załadowanego pliku via engine).
        Komentarze i guardy w metodach.
        """
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
        self.title_label.setToolTip("Tytuł i artysta załadowanego pliku audio. EFEKT: pokazuje metadane z Track (z DB lub filename). Upuść inny plik by zmienić załadowany plik (load = FILE op).")
        header.addWidget(self.title_label, 1)

        # Compact spin indicator (pilot-like, hidden by default; shown+spins in compact+play)
        self._spin_indicator = _CompactSpinIndicator(self, size=20)
        self._spin_indicator.setVisible(False)
        header.addWidget(self._spin_indicator, 0)

        self.bpm_label = QtWidgets.QLabel("— BPM")
        self.bpm_label.setStyleSheet(get_bpm_label_stylesheet())
        self.bpm_label.setAlignment(
            QtCore.Qt.AlignmentFlag.AlignRight
            | QtCore.Qt.AlignmentFlag.AlignVCenter)
        self.bpm_label.setMinimumWidth(100)
        self.bpm_label.setToolTip("BPM utworu (z metadanych lub analizy). EFEKT: wpływa na beatgrid waveformu. Wartość z pliku/DB, nie zmienia pliku.")
        header.addWidget(self.bpm_label, 0)

        layout.addLayout(header)

        # === DOMINANT WAVEFORM (stretch 7, minHeight 260+) ===
        self.waveform = WaveformWidget()
        min_h = BOOTH_SIZES.get("waveform_min_height_single", 260)
        self.waveform.setMinimumHeight(min_h)
        self.waveform.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding
        )
        # Expand tooltip on wave for EFFECT (file/stream + drag)
        self.waveform.setToolTip(
            "Waveform: Click=seek (strumień) • Double-click=seek + set main CUE (dla play near0). "
            "EFEKT: zmienia pozycję w streamie z załadowanego PLIKU (nie load nowego pliku). "
            "Drag&drop z biblioteki ładuje nowy PLIK. Shift+click ignorowane w odt (no advanced)."
        )
        layout.addWidget(self.waveform, 7)

        # === TIME (center, fixed, 0 stretch, 18px mono) ===
        self.time_label = QtWidgets.QLabel("0:00 / 0:00")
        self.time_label.setStyleSheet(get_time_label_stylesheet())
        self.time_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.time_label.setToolTip("Pozycja / czas trwania. EFEKT: aktualizowane z playhead streamu (timer 40ms z engine state). Nie wpływa na plik.")
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
        self.status_label.setToolTip("Status decku (load/play/cue/set). EFEKT: informacyjny; nie wykonuje akcji. File ops w load, stream ops w transport.")
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
        if hasattr(self, "_spin_indicator"):
            self._spin_indicator.stop()

    def resizeEvent(self, event):
        """Scalability polish (per SZPIEG/Plan): dynamic on resize (multi-res, stretch).
        Zachowuje air, dominant wave, no-overlap. W compact mniejsze bazowe.
        """
        super().resizeEvent(event)
        # Dynamic tweak: ensure min wave respects current size in non-compact
        if not self._compact and hasattr(self, "waveform"):
            try:
                avail_h = max(60, self.height() - 120)  # rough for header+time+trans+status+air
                cur_min = self.waveform.minimumHeight()
                target = min(260, max(120, avail_h))
                if target != cur_min:
                    self.waveform.setMinimumHeight(target)
            except Exception:
                pass
        # Ensure spin size scales a bit in compact
        if self._compact and hasattr(self, "_spin_indicator"):
            try:
                s = max(16, min(28, self.width() // 30))
                self._spin_indicator.setFixedSize(s, s)
            except Exception:
                pass

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
        # Compact anim react (spin CD only when playing + compact)
        self._update_compact_play_state(playing)

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
            # Highlight for drag UX (per spec: highlight+position safety)
            self.setStyleSheet(
                self._normal_stylesheet.replace(
                    "border: 1px solid #2a3442;",
                    "border: 2px solid #00e0ff; background-color: #1a212c;"
                ) if hasattr(self, "_normal_stylesheet") else get_deck_panel_stylesheet()
            )
            pos = event.position().toPoint() if hasattr(event, "position") else event.pos()
            logger.debug(f"Odt dragEnter at pos {pos} (mime ok, FILE load pending)")
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragLeaveEvent(self, event: QtGui.QDragLeaveEvent) -> None:
        # Reset highlight
        if hasattr(self, "_normal_stylesheet"):
            self.setStyleSheet(self._normal_stylesheet)
        super().dragLeaveEvent(event)

    def dropEvent(self, event: QtGui.QDropEvent) -> None:
        # Reset highlight on drop
        if hasattr(self, "_normal_stylesheet"):
            self.setStyleSheet(self._normal_stylesheet)
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
            pos = event.position().toPoint() if hasattr(event, "position") else event.pos()
            logger.debug(f"Odt drop at pos {pos} -> load FILE {paths[0]}")
            # Safety (lock/prompt per spec): confirm if stream playing (FILE load during playback)
            if getattr(self, "_is_playing", False):
                try:
                    from PyQt6.QtWidgets import QMessageBox
                    resp = QMessageBox.question(
                        self, "Odtwarzacz — Safety",
                        "Trwa odtwarzanie (stream). Załadować nowy PLIK i zatrzymać?\n(EFEKT: stop + load nowego pliku z cue=0)",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                        QMessageBox.StandardButton.No
                    )
                    if resp != QMessageBox.StandardButton.Yes:
                        event.acceptProposedAction()
                        return
                except Exception:
                    pass  # non-fatal, proceed
            self._load_dropped_track(paths[0])
        event.acceptProposedAction()

    def _load_dropped_track(self, path: str) -> None:
        """Pełny lookup z repo jak w dj_player_window._load_dropped_track.
        To jest FILE op: drop = załaduj PLIK (lookup DB, set current_track, waveform token, cue=0).
        Po tym transport (play) używa STREAMU z pliku.
        Drag highlight/position obsługiwane przez mime w dragEnter/drop + parent window.
        """
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

    # ------------------------------------------------------------------
    # Compact mode (pilot-like) + animated indicator (per SZPIEG Build Spec step 3)
    # set_compact_mode, collapse sizes, react to play_state, spin CD-like.
    # Modular: sizes from styles.BOOTH_SIZES compact_*, anim self contained.
    # ------------------------------------------------------------------
    def set_compact_mode(self, compact: bool) -> None:
        """Włącz/wyłącz tryb compact (mały pilot). Zmienia rozmiary, fonty, min wave, pokazuje spin ind.
        Zachowuje cue logic, air (mniejsze), drag, scalability.
        Toggle z dj_player_window (przycisk).
        """
        if self._compact == bool(compact):
            return
        self._compact = bool(compact)
        try:
            if hasattr(self.controller, "set_compact_mode"):
                self.controller.set_compact_mode(compact)
        except Exception:
            pass
        self._apply_compact_ui()

    def _apply_compact_ui(self) -> None:
        compact = self._compact
        sizes = BOOTH_SIZES
        if compact:
            # Collapse sizes (pilot-like mini)
            play_s = sizes.get("compact_transport_play", (52, 32))
            cue_s = sizes.get("compact_transport_cue", (42, 28))
            stop_s = sizes.get("compact_transport_stop", (36, 28))
            wave_min = sizes.get("compact_waveform_min_height", 80)
            bpm_f = sizes.get("compact_bpm_font", 14)
            title_f = sizes.get("compact_title_font", 11)
            time_f = sizes.get("compact_time_font", 10)
            stat_f = sizes.get("compact_status_font", 9)
            # smaller margins for pilot
            self.layout().setContentsMargins(8, 6, 8, 6)
            self.layout().setSpacing(6)
        else:
            play_s = sizes.get("transport_play", (96, 58))
            cue_s = sizes.get("transport_cue", (78, 52))
            stop_s = sizes.get("transport_stop", (68, 52))
            wave_min = sizes.get("waveform_min_height_single", 260)
            bpm_f = 32
            title_f = 18
            time_f = 16
            stat_f = 11
            self.layout().setContentsMargins(32, 24, 32, 24)
            self.layout().setSpacing(18)

        # Apply transport sizes
        if hasattr(self, "play_btn"):
            self.play_btn.setFixedSize(*play_s)
        if hasattr(self, "cue_btn"):
            self.cue_btn.setFixedSize(*cue_s)
        if hasattr(self, "stop_btn"):
            self.stop_btn.setFixedSize(*stop_s)

        # Wave min (dominant but smaller in compact)
        if hasattr(self, "waveform"):
            self.waveform.setMinimumHeight(wave_min)

        # Fonts
        if hasattr(self, "title_label"):
            self.title_label.setStyleSheet(
                f"font-size: {title_f}px; font-weight: 700; "
                f"color: {BOOTH_COLORS['text_primary']};")
        if hasattr(self, "bpm_label"):
            self.bpm_label.setStyleSheet(
                f"color: {BOOTH_COLORS['accent']}; font-size: {bpm_f}px; font-weight: 900; "
                "font-family: \"Consolas\", \"JetBrains Mono\", monospace;"
            )
        if hasattr(self, "time_label"):
            self.time_label.setStyleSheet(
                f"color: {BOOTH_COLORS['text_secondary']}; font-size: {time_f}px; font-weight: 700; "
                "font-family: \"Consolas\", \"JetBrains Mono\", monospace;"
            )
        if hasattr(self, "status_label"):
            self.status_label.setStyleSheet(
                f"color: {BOOTH_COLORS.get('text_muted', '#6b7688')}; font-size: {stat_f}px;"
            )

        # Spin indicator visible only in compact (pilot)
        if hasattr(self, "_spin_indicator"):
            self._spin_indicator.setVisible(compact)
            if not compact:
                self._spin_indicator.stop()

        self.updateGeometry()

    def _update_compact_play_state(self, playing: bool) -> None:
        """React to play_state for anim (spin when playing in compact)."""
        if hasattr(self, "_spin_indicator") and self._compact:
            if playing:
                self._spin_indicator.start()
            else:
                self._spin_indicator.stop()
