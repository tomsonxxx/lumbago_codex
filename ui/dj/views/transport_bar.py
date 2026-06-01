"""
ui/dj/views/transport_bar.py

TransportBar – duże przyciski PLAY / CUE / STOP + ewentualnie czas.

Prosta wersja szkieletowa (faza 1).
Używa wyłącznie stylów z styles.py.
Emituje sygnały do kontrolera.

W kolejnych iteracjach: integracja z kontrolerem + duże rozmiary z BOOTH_SIZES.
"""

from __future__ import annotations

from PyQt6 import QtCore, QtWidgets

from ui.dj.styles import (
    BOOTH_SIZES,
    get_transport_button_stylesheet,
    get_time_label_stylesheet,
)


class TransportBar(QtWidgets.QWidget):
    """
    Pasek transportu (duże przyciski booth).

    Sygnały:
    - play_clicked()
    - cue_clicked()
    - stop_clicked()
    """

    play_clicked = QtCore.pyqtSignal()
    cue_clicked = QtCore.pyqtSignal()
    stop_clicked = QtCore.pyqtSignal()

    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)

        layout = QtWidgets.QHBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addStretch(1)

        # PLAY – największy
        play_size = BOOTH_SIZES.get("transport_play", (96, 58))
        self.play_btn = QtWidgets.QPushButton("▶  ODTWÓRZ")
        self.play_btn.setFixedSize(*play_size)
        self.play_btn.setStyleSheet(get_transport_button_stylesheet("play"))
        self.play_btn.clicked.connect(self.play_clicked)

        # CUE
        cue_size = BOOTH_SIZES.get("transport_cue", (78, 52))
        self.cue_btn = QtWidgets.QPushButton("CUE")
        self.cue_btn.setFixedSize(*cue_size)
        self.cue_btn.setStyleSheet(get_transport_button_stylesheet("cue"))
        self.cue_btn.clicked.connect(self.cue_clicked)

        # STOP
        stop_size = BOOTH_SIZES.get("transport_stop", (68, 52))
        self.stop_btn = QtWidgets.QPushButton("■  STOP")
        self.stop_btn.setFixedSize(*stop_size)
        self.stop_btn.setStyleSheet(get_transport_button_stylesheet("stop"))
        self.stop_btn.clicked.connect(self.stop_clicked)

        layout.addWidget(self.cue_btn)
        layout.addWidget(self.play_btn)
        layout.addWidget(self.stop_btn)
        layout.addStretch(1)

        # PPM menu na każdym przycisku (Krok 4)
        self._setup_context_menus()

        # Opcjonalny czas (później podłączony do sygnałów kontrolera)
        self.time_label = QtWidgets.QLabel("0:00 / 0:00")
        self.time_label.setStyleSheet(get_time_label_stylesheet())
        self.time_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        # Na razie ukryty – dodamy w pełnej integracji
        self.time_label.hide()

    def set_playing(self, playing: bool) -> None:
        """Zmienia tekst przycisku play."""
        self.play_btn.setText("❚❚  PAUZA" if playing else "▶  ODTWÓRZ")

    def set_time_text(self, text: str) -> None:
        self.time_label.setText(text)

    def _setup_context_menus(self):
        """Indywidualne menu kontekstowe PPM na przyciskach transportowych (Krok 4)."""
        self.play_btn.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.play_btn.customContextMenuRequested.connect(self._show_play_menu)

        self.cue_btn.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.cue_btn.customContextMenuRequested.connect(self._show_cue_menu)

        self.stop_btn.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.stop_btn.customContextMenuRequested.connect(self._show_stop_menu)

    def _show_play_menu(self, pos):
        menu = QtWidgets.QMenu(self)
        menu.addAction("Odtwórz od CUE")
        menu.addAction("Odtwórz od początku")
        menu.addAction("Odtwórz od aktualnej pozycji")
        menu.exec(self.play_btn.mapToGlobal(pos))

    def _show_cue_menu(self, pos):
        menu = QtWidgets.QMenu(self)
        menu.addAction("Ustaw CUE w aktualnej pozycji")
        menu.addAction("Skocz do CUE")
        menu.addAction("Wyczyść CUE")
        menu.exec(self.cue_btn.mapToGlobal(pos))

    def _show_stop_menu(self, pos):
        menu = QtWidgets.QMenu(self)
        menu.addAction("Stop + powrót do CUE")
        menu.addAction("Stop + powrót do 0")
        menu.addAction("Tylko Stop")
        menu.exec(self.stop_btn.mapToGlobal(pos))
