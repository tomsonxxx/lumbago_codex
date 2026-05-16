"""
Player widget dla Lumbago_Music.
WaveformWidget (QPainter Float32), HotcuePad (8 padów), PlayerWidget (QtMultimedia).
"""
from __future__ import annotations
import logging
from pathlib import Path
from typing import TYPE_CHECKING
from PyQt6 import QtCore, QtGui, QtWidgets
try:
    from PyQt6 import QtMultimedia
    _HAS_MULTIMEDIA = True
except ImportError:
    QtMultimedia = None  # type: ignore[assignment]
    _HAS_MULTIMEDIA = False

if TYPE_CHECKING:
    from core.models import Track, CuePoint
    from core.waveform import WaveformData

logger = logging.getLogger(__name__)

HOTCUE_COLORS = ["#39ff14","#63f2ff","#ff6bd5","#ffaa00","#ff4f4f","#aa55ff","#ffffff","#ff9500"]
PLAYHEAD_COLOR = "#ff3333"
LOOP_FILL_RGBA = (100, 180, 255, 40)


class WaveformWidget(QtWidgets.QWidget):
    seek_requested = QtCore.pyqtSignal(int)
    cue_set_at = QtCore.pyqtSignal(int, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(80)
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed)
        self.setMouseTracking(True)
        self.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self._peaks: list[float] = []
        self._duration_ms: int = 0
        self._playhead_ms: int = 0
        self._cue_points: list = []
        self._loop_start_ms: int = -1
        self._loop_end_ms: int = -1
        self._hover_x: int = -1
        self._col_bg = QtGui.QColor("#0d1320")
        self._col_peak = QtGui.QColor("#63f2ff")
        self._col_rms = QtGui.QColor("#1e4a5a")
        self._col_playhead = QtGui.QColor(PLAYHEAD_COLOR)

    def load_waveform(self, waveform) -> None:
        if waveform and not waveform.is_empty():
            norm = waveform.normalized_peaks()
            self._peaks = list(norm)
            self._duration_ms = int(waveform.duration_s * 1000)
        else:
            self._peaks = []
            self._duration_ms = 0
        self._playhead_ms = 0
        self.update()

    def set_playhead(self, time_ms: int) -> None:
        if time_ms != self._playhead_ms:
            self._playhead_ms = time_ms
            self.update()

    def set_cue_points(self, cue_points: list) -> None:
        self._cue_points = list(cue_points)
        self.update()

    def set_loop(self, start_ms: int, end_ms: int) -> None:
        self._loop_start_ms = start_ms
        self._loop_end_ms = end_ms
        self.update()

    def clear_loop(self) -> None:
        self._loop_start_ms = -1
        self._loop_end_ms = -1
        self.update()

    def clear(self) -> None:
        self._peaks = []
        self._duration_ms = 0
        self._playhead_ms = 0
        self._cue_points = []
        self._loop_start_ms = -1
        self._loop_end_ms = -1
        self.update()

    def update_colors(self, bg: str, peak: str, rms: str) -> None:
        self._col_bg = QtGui.QColor(bg)
        self._col_peak = QtGui.QColor(peak)
        self._col_rms = QtGui.QColor(rms)
        self.update()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, False)
        w, h = self.width(), self.height()
        mid = h // 2
        painter.fillRect(0, 0, w, h, self._col_bg)

        if not self._peaks:
            painter.setPen(QtGui.QPen(self._col_rms, 1))
            painter.drawLine(0, mid, w, mid)
            self._draw_playhead(painter, w, h)
            painter.end()
            return

        n = len(self._peaks)
        pen_peak = QtGui.QPen(self._col_peak, 1)
        pen_rms = QtGui.QPen(self._col_rms, 1)
        for px in range(w):
            idx = int(px / w * n)
            if idx >= n:
                idx = n - 1
            amp = self._peaks[idx]
            ph = int(amp * mid * 0.9)
            rh = max(1, int(amp * mid * 0.4))
            painter.setPen(pen_rms)
            painter.drawLine(px, mid - rh, px, mid + rh)
            painter.setPen(pen_peak)
            painter.drawLine(px, mid - ph, px, mid - rh)
            painter.drawLine(px, mid + rh, px, mid + ph)

        if self._loop_start_ms >= 0 and self._loop_end_ms > self._loop_start_ms and self._duration_ms > 0:
            lx1 = int(self._loop_start_ms / self._duration_ms * w)
            lx2 = int(self._loop_end_ms / self._duration_ms * w)
            painter.fillRect(lx1, 0, lx2 - lx1, h, QtGui.QColor(*LOOP_FILL_RGBA))

        if self._hover_x >= 0:
            painter.fillRect(self._hover_x, 0, 1, h, QtGui.QColor(255, 255, 255, 30))

        self._draw_cue_markers(painter, w, h)
        self._draw_playhead(painter, w, h)
        painter.end()

    def _draw_playhead(self, painter, w, h):
        if self._duration_ms <= 0:
            return
        px = max(0, min(int(self._playhead_ms / self._duration_ms * w), w - 1))
        painter.setPen(QtGui.QPen(self._col_playhead, 2))
        painter.drawLine(px, 0, px, h)

    def _draw_cue_markers(self, painter, w, h):
        if self._duration_ms <= 0:
            return
        ms = 8
        for cue in self._cue_points:
            idx = getattr(cue, 'hotcue_index', None)
            if idx is None or idx < 0:
                continue
            color_str = getattr(cue, 'color', None) or HOTCUE_COLORS[idx % len(HOTCUE_COLORS)]
            color = QtGui.QColor(color_str)
            px = max(0, min(int(cue.time_ms / self._duration_ms * w), w - 1))
            painter.setPen(QtGui.QPen(color, 1))
            painter.drawLine(px, 0, px, h)
            tri = QtGui.QPolygon([QtCore.QPoint(px-ms//2, h), QtCore.QPoint(px+ms//2, h), QtCore.QPoint(px, h-ms)])
            painter.setBrush(QtGui.QBrush(color))
            painter.setPen(QtCore.Qt.PenStyle.NoPen)
            painter.drawPolygon(tri)
            painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)

    def mousePressEvent(self, event):
        if self._duration_ms <= 0:
            return
        t = max(0, min(int(event.position().x() / self.width() * self._duration_ms), self._duration_ms))
        if event.modifiers() & QtCore.Qt.KeyboardModifier.ShiftModifier:
            self.cue_set_at.emit(0, t)
        else:
            self.seek_requested.emit(t)

    def mouseMoveEvent(self, event):
        self._hover_x = int(event.position().x())
        self.update()

    def leaveEvent(self, event):
        self._hover_x = -1
        self.update()


class HotcuePad(QtWidgets.QPushButton):
    cue_activated = QtCore.pyqtSignal(int)
    cue_set_requested = QtCore.pyqtSignal(int)
    cue_deleted = QtCore.pyqtSignal(int)

    def __init__(self, index: int, parent=None):
        super().__init__(parent)
        self.index = index
        self._color = HOTCUE_COLORS[index % len(HOTCUE_COLORS)]
        self._has_cue = False
        self._label = f"CUE {index + 1}"
        self.setFixedSize(64, 40)
        self.setToolTip(f"Hotcue {index+1}\nShift+klik=ustaw\nCtrl+klik=usuń")
        self._update_style()

    def set_cue(self, cue) -> None:
        if cue is not None:
            self._has_cue = True
            self._color = getattr(cue, 'color', None) or HOTCUE_COLORS[self.index % len(HOTCUE_COLORS)]
            self._label = getattr(cue, 'label', None) or f"CUE {self.index+1}"
        else:
            self._has_cue = False
            self._color = HOTCUE_COLORS[self.index % len(HOTCUE_COLORS)]
            self._label = f"CUE {self.index+1}"
        self._update_style()

    def _update_style(self):
        if self._has_cue:
            s = f"QPushButton{{background-color:{self._color};color:#000;border:none;border-radius:4px;font-size:9px;font-weight:bold;}}QPushButton:pressed{{background-color:#fff;}}"
        else:
            s = f"QPushButton{{background-color:#1a2235;color:{self._color};border:1px solid {self._color}44;border-radius:4px;font-size:9px;}}QPushButton:hover{{background-color:{self._color}22;border-color:{self._color};}}"
        self.setStyleSheet(s)
        self.setText(self._label[:8] if self._has_cue else f"·{self.index+1}·")

    def mousePressEvent(self, event):
        if event.modifiers() & QtCore.Qt.KeyboardModifier.ControlModifier:
            self.cue_deleted.emit(self.index)
        elif event.modifiers() & QtCore.Qt.KeyboardModifier.ShiftModifier:
            self.cue_set_requested.emit(self.index)
        else:
            self.cue_activated.emit(self.index)
        super().mousePressEvent(event)


class PlayerWidget(QtWidgets.QFrame):
    track_ended = QtCore.pyqtSignal()
    playback_position_changed = QtCore.pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty("player", True)
        self.setMinimumHeight(200)
        if _HAS_MULTIMEDIA:
            self._player = QtMultimedia.QMediaPlayer(self)
            self._audio_output = QtMultimedia.QAudioOutput(self)
            self._player.setAudioOutput(self._audio_output)
            self._audio_output.setVolume(0.8)
        else:
            self._player = None
            self._audio_output = None
        self._current_track = None
        self._cue_points: dict[int, object] = {}
        self._loop_a_ms: int = -1
        self._loop_b_ms: int = -1
        self._playhead_timer = QtCore.QTimer(self)
        self._playhead_timer.setInterval(16)
        self._playhead_timer.timeout.connect(self._update_playhead)
        self._build_ui()
        self._connect_signals()

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(6)
        self.waveform = WaveformWidget(self)
        self.waveform.setMinimumHeight(90)
        layout.addWidget(self.waveform)
        self._hotcue_pads: list[HotcuePad] = []
        grid = QtWidgets.QGridLayout()
        grid.setSpacing(4)
        for i in range(8):
            pad = HotcuePad(i, self)
            self._hotcue_pads.append(pad)
            grid.addWidget(pad, i // 4, i % 4)
        layout.addLayout(grid)
        transport = QtWidgets.QHBoxLayout()
        transport.setSpacing(6)
        self.btn_prev = self._mkbtn("⏮", 32)
        self.btn_play = self._mkbtn("▶", 44)
        self.btn_stop = self._mkbtn("⏹", 32)
        self.btn_next = self._mkbtn("⏭", 32)
        self.lbl_time = QtWidgets.QLabel("0:00 / 0:00")
        self.lbl_time.setStyleSheet("color:#8fb8d8;font-size:11px;font-family:monospace;")
        self.lbl_time.setMinimumWidth(100)
        self.slider_vol = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.slider_vol.setRange(0, 100)
        self.slider_vol.setValue(80)
        self.slider_vol.setMaximumWidth(100)
        self.btn_loop_a = self._mkbtn("A", 32)
        self.btn_loop_b = self._mkbtn("B", 32)
        self.btn_loop_clear = self._mkbtn("✕", 32)
        for w in [self.btn_prev, self.btn_play, self.btn_stop, self.btn_next, self.lbl_time]:
            transport.addWidget(w)
        transport.addStretch()
        for w in [QtWidgets.QLabel("🔁"), self.btn_loop_a, self.btn_loop_b, self.btn_loop_clear]:
            transport.addWidget(w)
        transport.addStretch()
        for w in [QtWidgets.QLabel("🔊"), self.slider_vol]:
            transport.addWidget(w)
        layout.addLayout(transport)

    @staticmethod
    def _mkbtn(text: str, w: int) -> QtWidgets.QPushButton:
        btn = QtWidgets.QPushButton(text)
        btn.setFixedWidth(w)
        btn.setFixedHeight(30)
        return btn

    def _connect_signals(self):
        if _HAS_MULTIMEDIA and self._player is not None:
            self._player.playbackStateChanged.connect(self._on_state_changed)
            self._player.mediaStatusChanged.connect(self._on_media_status)
            self._player.errorOccurred.connect(lambda e, m: logger.error("Player: %s %s", e, m))
        self.btn_play.clicked.connect(self.toggle_play)
        self.btn_stop.clicked.connect(self.stop)
        self.btn_loop_a.clicked.connect(self._set_loop_a)
        self.btn_loop_b.clicked.connect(self._set_loop_b)
        self.btn_loop_clear.clicked.connect(self._clear_loop)
        if _HAS_MULTIMEDIA and self._audio_output is not None:
            self.slider_vol.valueChanged.connect(lambda v: self._audio_output.setVolume(v / 100.0))
        self.waveform.seek_requested.connect(self.seek)
        self.waveform.cue_set_at.connect(self._on_cue_set_at)
        for pad in self._hotcue_pads:
            pad.cue_activated.connect(self._on_cue_activated)
            pad.cue_set_requested.connect(self._on_cue_set_requested)
            pad.cue_deleted.connect(self._on_cue_deleted)

    def load_track(self, track, waveform=None, cue_points=None):
        self._current_track = track
        self._cue_points = {}
        if waveform:
            self.waveform.load_waveform(waveform)
        else:
            self.waveform.clear()
        if cue_points:
            for cue in cue_points:
                idx = getattr(cue, 'hotcue_index', None)
                if idx is not None:
                    self._cue_points[idx] = cue
        self._refresh_pads()
        self.waveform.set_cue_points(list(self._cue_points.values()))
        p = Path(track.path)
        if p.exists() and self._player is not None:
            self._player.setSource(QtCore.QUrl.fromLocalFile(str(p)))
        self._loop_a_ms = -1
        self._loop_b_ms = -1
        self.waveform.clear_loop()

    def play(self):
        if self._player is not None: self._player.play()
        self._playhead_timer.start()
    def pause(self):
        if self._player is not None: self._player.pause()
        self._playhead_timer.stop()
    def toggle_play(self):
        if self._player is None:
            return
        PS = QtMultimedia.QMediaPlayer.PlaybackState
        if self._player.playbackState() == PS.PlayingState:
            self.pause()
        else:
            self.play()
    def stop(self):
        if self._player is not None: self._player.stop()
        self._playhead_timer.stop()
        self.waveform.set_playhead(0); self._update_time_label(0)
    def seek(self, t: int):
        if self._player is not None: self._player.setPosition(t)
        self.waveform.set_playhead(t); self._update_time_label(t)
    def set_volume(self, v: float):
        if self._audio_output is not None:
            self._audio_output.setVolume(max(0.0, min(1.0, v)))

    def _update_playhead(self):
        pos = self._player.position() if self._player is not None else 0
        self.waveform.set_playhead(pos)
        self._update_time_label(pos)
        self.playback_position_changed.emit(pos)
        if self._loop_a_ms >= 0 and self._loop_b_ms > self._loop_a_ms and pos >= self._loop_b_ms:
            self.seek(self._loop_a_ms)

    def _update_time_label(self, pos_ms: int):
        dur = (self._player.duration() if self._player is not None else 0) or 0
        def fmt(s): return f"{s//60}:{s%60:02d}"
        self.lbl_time.setText(f"{fmt(pos_ms//1000)} / {fmt(dur//1000)}")

    def _refresh_pads(self):
        for pad in self._hotcue_pads:
            pad.set_cue(self._cue_points.get(pad.index))

    def _set_loop_a(self):
        self._loop_a_ms = self._player.position() if self._player is not None else 0
        self._update_loop_overlay()
    def _set_loop_b(self):
        self._loop_b_ms = self._player.position() if self._player is not None else 0
        self._update_loop_overlay()
    def _clear_loop(self): self._loop_a_ms = -1; self._loop_b_ms = -1; self.waveform.clear_loop()
    def _update_loop_overlay(self):
        if self._loop_a_ms >= 0 and self._loop_b_ms > self._loop_a_ms:
            self.waveform.set_loop(self._loop_a_ms, self._loop_b_ms)

    def _on_cue_activated(self, idx: int):
        cue = self._cue_points.get(idx)
        if cue:
            self.seek(cue.time_ms)

    def _on_cue_set_requested(self, idx: int):
        self._set_cue_at(idx, self._player.position() if self._player is not None else 0)
    def _on_cue_set_at(self, idx: int, t: int): self._set_cue_at(idx, t)

    def _set_cue_at(self, idx: int, t: int):
        from core.models import CuePoint
        cue = CuePoint(time_ms=t, cue_type="hotcue", hotcue_index=idx,
                       label=f"Cue {idx+1}", color=HOTCUE_COLORS[idx % len(HOTCUE_COLORS)])
        self._cue_points[idx] = cue
        self._refresh_pads()
        self.waveform.set_cue_points(list(self._cue_points.values()))

    def _on_cue_deleted(self, idx: int):
        self._cue_points.pop(idx, None)
        self._refresh_pads()
        self.waveform.set_cue_points(list(self._cue_points.values()))

    def _on_state_changed(self, state):
        if not _HAS_MULTIMEDIA:
            return
        PS = QtMultimedia.QMediaPlayer.PlaybackState
        if state == PS.PlayingState:
            self.btn_play.setText("⏸"); self._playhead_timer.start()
        else:
            self.btn_play.setText("▶")
            if state == PS.StoppedState:
                self._playhead_timer.stop()

    def _on_media_status(self, status):
        if not _HAS_MULTIMEDIA:
            return
        if status == QtMultimedia.QMediaPlayer.MediaStatus.EndOfMedia:
            self._playhead_timer.stop(); self.track_ended.emit()
