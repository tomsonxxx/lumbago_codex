"""
Lumbago Music AI — Panel odtwarzacza
======================================
Mini player z waveformem, kontrolkami transportu i VU metrem.
"""

import logging

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QLabel, QSlider,
)

logger = logging.getLogger(__name__)


class PlayerPanel(QWidget):
    """Panel odtwarzacza DJ z waveformem i transportem."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMaximumHeight(180)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(4)

        # Waveform placeholder
        from lumbago_app.ui.widgets.mini_waveform import MiniWaveform
        self._waveform = MiniWaveform()
        self._waveform.setMinimumHeight(60)
        layout.addWidget(self._waveform)

        # Transport controls
        transport = QHBoxLayout()

        self._btn_prev = QPushButton("⏮")
        self._btn_play = QPushButton("▶")
        self._btn_stop = QPushButton("⏹")
        self._btn_next = QPushButton("⏭")

        for btn in (self._btn_prev, self._btn_play, self._btn_stop, self._btn_next):
            btn.setFixedWidth(40)
            transport.addWidget(btn)

        transport.addSpacing(8)

        # Position slider
        self._pos_slider = QSlider(Qt.Orientation.Horizontal)
        self._pos_slider.setRange(0, 1000)
        transport.addWidget(self._pos_slider, stretch=1)

        # Time label
        self._time_label = QLabel("0:00 / 0:00")
        self._time_label.setFixedWidth(90)
        transport.addWidget(self._time_label)

        # Volume
        vol_label = QLabel("VOL")
        vol_label.setStyleSheet("color: #606070; font-size: 10px;")
        transport.addWidget(vol_label)

        self._vol_slider = QSlider(Qt.Orientation.Horizontal)
        self._vol_slider.setRange(0, 100)
        self._vol_slider.setValue(80)
        self._vol_slider.setFixedWidth(80)
        transport.addWidget(self._vol_slider)

        layout.addLayout(transport)

        # Track info
        self._track_label = QLabel("— Brak aktywnego utworu —")
        self._track_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._track_label.setStyleSheet("color: #606070; font-size: 11px;")
        layout.addWidget(self._track_label)

        # Podpięcie przycisków
        self._btn_play.clicked.connect(self._on_play_pause)
        self._btn_stop.clicked.connect(self._on_stop)

    def load_track(self, file_path: str) -> None:
        """
        Ładuje utwór do odtwarzacza.

        Args:
            file_path: Ścieżka do pliku audio.
        """
        raise NotImplementedError(
            "PlayerPanel.load_track() — do implementacji w FAZIE 2.\n"
            "Plan: QMediaPlayer lub pydub backend."
        )

    def _on_play_pause(self) -> None:
        """Przełącza odtwarzanie/pauzę."""
        logger.debug("Play/Pause — do implementacji")

    def _on_stop(self) -> None:
        """Zatrzymuje odtwarzanie."""
        logger.debug("Stop — do implementacji")
