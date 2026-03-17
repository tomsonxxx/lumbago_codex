from __future__ import annotations

from PyQt6 import QtCore, QtGui, QtWidgets

from lumbago_app.core.models import Track


def _format_time(ms: int) -> str:
    """Formatuj milisekundy jako mm:ss."""
    total_sec = max(0, ms // 1000)
    minutes = total_sec // 60
    seconds = total_sec % 60
    return f"{minutes:02d}:{seconds:02d}"


_CARD_STYLE = """
QFrame#Card {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 rgba(13, 17, 42, 0.95), stop:1 rgba(10, 13, 26, 0.9));
    border: 1px solid rgba(0, 212, 255, 0.15);
    border-radius: 12px;
    padding: 12px;
}
"""

_SEEKBAR_STYLE = """
QSlider::groove:horizontal {
    height: 6px;
    background: #1a1f3a;
    border-radius: 3px;
}
QSlider::sub-page:horizontal {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #00d4ff, stop:1 #8b5cf6);
    border-radius: 3px;
}
QSlider::handle:horizontal {
    width: 14px;
    height: 14px;
    margin: -4px 0;
    background: #00d4ff;
    border-radius: 7px;
    border: 2px solid #0a0d1a;
}
QSlider::handle:horizontal:hover {
    background: #33ddff;
    width: 16px;
    height: 16px;
    margin: -5px 0;
    border-radius: 8px;
}
"""

_VOLUME_STYLE = """
QSlider::groove:horizontal {
    height: 4px;
    background: #1a1f3a;
    border-radius: 2px;
}
QSlider::sub-page:horizontal {
    background: #8b5cf6;
    border-radius: 2px;
}
QSlider::handle:horizontal {
    width: 12px;
    height: 12px;
    margin: -4px 0;
    background: #8b5cf6;
    border-radius: 6px;
    border: 2px solid #0a0d1a;
}
QSlider::handle:horizontal:hover {
    background: #a78bfa;
}
"""

_TRANSPORT_BTN_STYLE = """
QPushButton {
    background: rgba(13, 17, 42, 0.8);
    border: 1px solid rgba(0, 212, 255, 0.25);
    border-radius: 18px;
    color: #e6f7ff;
    font-size: 16px;
    min-width: 36px;
    min-height: 36px;
    max-width: 36px;
    max-height: 36px;
    padding: 0px;
}
QPushButton:hover {
    background: rgba(0, 212, 255, 0.15);
    border-color: #00d4ff;
}
QPushButton:pressed {
    background: rgba(0, 212, 255, 0.25);
}
"""

_PLAY_BTN_STYLE = """
QPushButton {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #00d4ff, stop:1 #0099cc);
    border: none;
    border-radius: 24px;
    color: #0a0d1a;
    font-size: 22px;
    font-weight: bold;
    min-width: 48px;
    min-height: 48px;
    max-width: 48px;
    max-height: 48px;
    padding: 0px;
}
QPushButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #33ddff, stop:1 #00bbee);
}
QPushButton:pressed {
    background: #0099cc;
}
"""

_META_CARD_STYLE = """
QFrame#Card {
    background: rgba(13, 17, 42, 0.85);
    border: 1px solid rgba(139, 92, 246, 0.2);
    border-radius: 8px;
    padding: 8px 12px;
}
"""


class PlayerPage(QtWidgets.QWidget):
    """Strona odtwarzacza — widżet inline dla QStackedWidget."""

    play_requested = QtCore.pyqtSignal(str)
    next_requested = QtCore.pyqtSignal()
    prev_requested = QtCore.pyqtSignal()

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setStyleSheet("background: #0a0d1a;")
        self._current_track: Track | None = None
        self._is_playing = False
        self._seeking = False
        self._build_ui()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        root = QtWidgets.QHBoxLayout(self)
        root.setContentsMargins(40, 30, 40, 30)
        root.setSpacing(32)

        # ---- lewa / centralna kolumna ----
        center_col = QtWidgets.QVBoxLayout()
        center_col.setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter)
        center_col.setSpacing(16)

        # Artwork
        self._artwork_label = QtWidgets.QLabel()
        self._artwork_label.setFixedSize(300, 300)
        self._artwork_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self._artwork_label.setStyleSheet(
            "border-radius: 16px; border: 1px solid rgba(0, 212, 255, 0.15);"
        )
        self._set_placeholder_artwork()
        center_col.addWidget(
            self._artwork_label, alignment=QtCore.Qt.AlignmentFlag.AlignHCenter
        )

        # Track info
        self._title_label = QtWidgets.QLabel("Brak utworu")
        self._title_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self._title_label.setStyleSheet(
            "color: #e6f7ff; font-size: 20px; font-weight: bold; background: transparent;"
        )
        self._title_label.setWordWrap(True)
        center_col.addWidget(self._title_label)

        self._artist_label = QtWidgets.QLabel("Nieznany artysta")
        self._artist_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self._artist_label.setStyleSheet(
            "color: #94a3b8; font-size: 14px; background: transparent;"
        )
        center_col.addWidget(self._artist_label)

        self._album_label = QtWidgets.QLabel("")
        self._album_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self._album_label.setStyleSheet(
            "color: #64748b; font-size: 12px; background: transparent;"
        )
        center_col.addWidget(self._album_label)

        center_col.addSpacing(8)

        # Seek bar
        self._seek_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self._seek_slider.setRange(0, 1000)
        self._seek_slider.setValue(0)
        self._seek_slider.setStyleSheet(_SEEKBAR_STYLE)
        self._seek_slider.setFixedWidth(340)
        self._seek_slider.sliderPressed.connect(self._on_seek_pressed)
        self._seek_slider.sliderReleased.connect(self._on_seek_released)
        center_col.addWidget(
            self._seek_slider, alignment=QtCore.Qt.AlignmentFlag.AlignHCenter
        )

        # Time labels
        time_row = QtWidgets.QHBoxLayout()
        time_row.setContentsMargins(0, 0, 0, 0)
        self._time_current = QtWidgets.QLabel("00:00")
        self._time_current.setStyleSheet(
            "color: #94a3b8; font-size: 11px; background: transparent;"
        )
        self._time_total = QtWidgets.QLabel("00:00")
        self._time_total.setStyleSheet(
            "color: #94a3b8; font-size: 11px; background: transparent;"
        )
        time_container = QtWidgets.QWidget()
        time_container.setFixedWidth(340)
        time_container.setStyleSheet("background: transparent;")
        time_layout = QtWidgets.QHBoxLayout(time_container)
        time_layout.setContentsMargins(0, 0, 0, 0)
        time_layout.addWidget(self._time_current)
        time_layout.addStretch()
        time_layout.addWidget(self._time_total)
        center_col.addWidget(
            time_container, alignment=QtCore.Qt.AlignmentFlag.AlignHCenter
        )

        center_col.addSpacing(4)

        # Transport controls
        transport_row = QtWidgets.QHBoxLayout()
        transport_row.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        transport_row.setSpacing(16)

        self._btn_prev = QtWidgets.QPushButton("\u23EE")
        self._btn_prev.setStyleSheet(_TRANSPORT_BTN_STYLE)
        self._btn_prev.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self._btn_prev.setToolTip("Poprzedni utwór")
        self._btn_prev.clicked.connect(self.prev_requested.emit)

        self._btn_play = QtWidgets.QPushButton("\u25B6")
        self._btn_play.setStyleSheet(_PLAY_BTN_STYLE)
        self._btn_play.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self._btn_play.setToolTip("Odtwórz / Pauza")
        self._btn_play.clicked.connect(self._on_play_clicked)

        self._btn_next = QtWidgets.QPushButton("\u23ED")
        self._btn_next.setStyleSheet(_TRANSPORT_BTN_STYLE)
        self._btn_next.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self._btn_next.setToolTip("Następny utwór")
        self._btn_next.clicked.connect(self.next_requested.emit)

        transport_row.addWidget(self._btn_prev)
        transport_row.addWidget(self._btn_play)
        transport_row.addWidget(self._btn_next)

        center_col.addLayout(transport_row)

        center_col.addSpacing(8)

        # Volume control
        vol_row = QtWidgets.QHBoxLayout()
        vol_row.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        vol_row.setSpacing(8)

        vol_icon = QtWidgets.QLabel("\U0001F50A")
        vol_icon.setStyleSheet(
            "color: #94a3b8; font-size: 14px; background: transparent;"
        )
        self._volume_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self._volume_slider.setRange(0, 100)
        self._volume_slider.setValue(80)
        self._volume_slider.setFixedWidth(140)
        self._volume_slider.setStyleSheet(_VOLUME_STYLE)

        vol_row.addWidget(vol_icon)
        vol_row.addWidget(self._volume_slider)

        center_col.addLayout(vol_row)
        center_col.addStretch()

        root.addLayout(center_col, stretch=1)

        # ---- prawa kolumna: metadane ----
        self._meta_col = QtWidgets.QVBoxLayout()
        self._meta_col.setSpacing(10)
        self._meta_col.setAlignment(
            QtCore.Qt.AlignmentFlag.AlignTop | QtCore.Qt.AlignmentFlag.AlignLeft
        )

        meta_header = QtWidgets.QLabel("Szczegóły utworu")
        meta_header.setStyleSheet(
            "color: #e6f7ff; font-size: 14px; font-weight: bold; "
            "background: transparent; margin-bottom: 4px;"
        )
        self._meta_col.addWidget(meta_header)

        self._meta_cards: dict[str, QtWidgets.QLabel] = {}
        meta_fields = [
            ("bpm", "BPM"),
            ("key", "Tonacja"),
            ("format", "Format"),
            ("genre", "Gatunek"),
            ("mood", "Nastrój"),
        ]
        for field_key, field_label in meta_fields:
            card = self._make_meta_card(field_label, "—")
            self._meta_cards[field_key] = card
            self._meta_col.addWidget(card)

        self._meta_col.addStretch()

        meta_widget = QtWidgets.QWidget()
        meta_widget.setFixedWidth(200)
        meta_widget.setStyleSheet("background: transparent;")
        meta_widget.setLayout(self._meta_col)
        root.addWidget(meta_widget)

    def _make_meta_card(self, label: str, value: str) -> QtWidgets.QFrame:
        """Tworzy małą kartę z etykietą i wartością metadanych."""
        frame = QtWidgets.QFrame()
        frame.setObjectName("Card")
        frame.setStyleSheet(_META_CARD_STYLE)
        frame.setFixedWidth(180)

        layout = QtWidgets.QVBoxLayout(frame)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(2)

        lbl = QtWidgets.QLabel(label)
        lbl.setStyleSheet(
            "color: #64748b; font-size: 10px; text-transform: uppercase; "
            "background: transparent; border: none;"
        )

        val = QtWidgets.QLabel(value)
        val.setObjectName("metaValue")
        val.setStyleSheet(
            "color: #e6f7ff; font-size: 13px; font-weight: bold; "
            "background: transparent; border: none;"
        )

        layout.addWidget(lbl)
        layout.addWidget(val)
        return frame

    def _set_placeholder_artwork(self) -> None:
        """Ustawia placeholder okładki z gradientem i ikoną nuty."""
        pixmap = QtGui.QPixmap(300, 300)
        painter = QtGui.QPainter(pixmap)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)

        grad = QtGui.QLinearGradient(0, 0, 300, 300)
        grad.setColorAt(0.0, QtGui.QColor("#0d112a"))
        grad.setColorAt(0.5, QtGui.QColor("#1a1040"))
        grad.setColorAt(1.0, QtGui.QColor("#0a0d1a"))
        painter.fillRect(0, 0, 300, 300, grad)

        # Ikona nuty muzycznej
        painter.setPen(QtCore.Qt.PenStyle.NoPen)
        painter.setBrush(QtGui.QColor(0, 212, 255, 40))
        painter.drawEllipse(110, 80, 80, 80)

        font = QtGui.QFont("Segoe UI", 64)
        painter.setFont(font)
        painter.setPen(QtGui.QColor(0, 212, 255, 80))
        painter.drawText(
            QtCore.QRect(0, 0, 300, 300),
            QtCore.Qt.AlignmentFlag.AlignCenter,
            "\u266B",
        )

        painter.end()
        self._artwork_label.setPixmap(pixmap)

    # ------------------------------------------------------------------
    # Publiczne metody
    # ------------------------------------------------------------------

    def set_track(self, track: Track) -> None:
        """Aktualizuje wyświetlane informacje o utworze."""
        self._current_track = track
        self._title_label.setText(track.title or "Nieznany tytuł")
        self._artist_label.setText(track.artist or "Nieznany artysta")
        self._album_label.setText(track.album or "")

        # Metadane
        meta_map = {
            "bpm": f"{track.bpm:.1f}" if track.bpm else "—",
            "key": track.key or "—",
            "format": (track.format or "—").upper(),
            "genre": track.genre or "—",
            "mood": track.mood or "—",
        }
        for key, val in meta_map.items():
            card = self._meta_cards.get(key)
            if card:
                val_label = card.findChild(QtWidgets.QLabel, "metaValue")
                if val_label:
                    val_label.setText(val)

        # Czas trwania
        if track.duration:
            self._time_total.setText(_format_time(track.duration))
        else:
            self._time_total.setText("00:00")

        self._seek_slider.setValue(0)
        self._time_current.setText("00:00")

        # Okładka
        if track.artwork_path:
            pm = QtGui.QPixmap(track.artwork_path)
            if not pm.isNull():
                self.set_artwork(pm)
            else:
                self._set_placeholder_artwork()
        else:
            self._set_placeholder_artwork()

    def set_playing(self, is_playing: bool) -> None:
        """Przełącza ikonę przycisku odtwarzania/pauzy."""
        self._is_playing = is_playing
        self._btn_play.setText("\u23F8" if is_playing else "\u25B6")
        self._btn_play.setToolTip("Pauza" if is_playing else "Odtwórz")

    def set_position(self, current_ms: int, total_ms: int) -> None:
        """Aktualizuje pasek postępu i etykiety czasu."""
        if self._seeking:
            return
        self._time_current.setText(_format_time(current_ms))
        self._time_total.setText(_format_time(total_ms))
        if total_ms > 0:
            self._seek_slider.setValue(int(current_ms * 1000 / total_ms))
        else:
            self._seek_slider.setValue(0)

    def set_artwork(self, pixmap: QtGui.QPixmap | None) -> None:
        """Ustawia okładkę albumu."""
        if pixmap is None or pixmap.isNull():
            self._set_placeholder_artwork()
            return
        scaled = pixmap.scaled(
            300,
            300,
            QtCore.Qt.AspectRatioMode.KeepAspectRatio,
            QtCore.Qt.TransformationMode.SmoothTransformation,
        )
        self._artwork_label.setPixmap(scaled)

    # ------------------------------------------------------------------
    # Sloty wewnętrzne
    # ------------------------------------------------------------------

    def _on_play_clicked(self) -> None:
        if self._current_track:
            self.play_requested.emit(self._current_track.path)

    def _on_seek_pressed(self) -> None:
        self._seeking = True

    def _on_seek_released(self) -> None:
        self._seeking = False
