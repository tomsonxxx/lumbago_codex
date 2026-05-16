from __future__ import annotations

from pathlib import Path

from PyQt6 import QtWidgets, QtGui
from ui.widgets import apply_dialog_fade, dialog_icon_pixmap

from services.xml_converter import export_virtualdj_xml, parse_rekordbox_xml


class XmlConverterDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Konwerter XML")
        self.setMinimumSize(720, 420)
        apply_dialog_fade(self)
        self._tracks = []
        self._build_ui()

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        card = QtWidgets.QFrame()
        card.setObjectName("DialogCard")
        card_layout = QtWidgets.QVBoxLayout(card)
        card_layout.setContentsMargins(16, 14, 16, 16)
        card_layout.setSpacing(10)
        layout.addWidget(card)
        layout = card_layout

        title_row = QtWidgets.QHBoxLayout()
        title_icon = QtWidgets.QLabel()
        title_icon.setPixmap(dialog_icon_pixmap(18))
        title_icon.setFixedSize(20, 20)
        title = QtWidgets.QLabel(self.windowTitle())
        title.setObjectName("DialogTitle")
        title_row.addWidget(title_icon)
        title_row.addWidget(title)
        title_row.addStretch(1)
        layout.addLayout(title_row)

        row = QtWidgets.QHBoxLayout()
        self.input_path = QtWidgets.QLineEdit()
        self.input_path.setPlaceholderText("Wybierz plik Rekordbox XML")
        row.addWidget(self.input_path, 1)
        browse_btn = QtWidgets.QPushButton("Wybierz")
        browse_btn.clicked.connect(self._browse)
        row.addWidget(browse_btn)
        layout.addLayout(row)

        self.status = QtWidgets.QLabel("Brak pliku")
        layout.addWidget(self.status)

        buttons = QtWidgets.QHBoxLayout()
        self.parse_btn = QtWidgets.QPushButton("Wczytaj i przelicz")
        self.parse_btn.clicked.connect(self._parse)
        self.export_btn = QtWidgets.QPushButton("Eksportuj do VirtualDJ")
        self.export_btn.clicked.connect(self._export)
        self.close_btn = QtWidgets.QPushButton("Zamknij")
        self.close_btn.clicked.connect(self.reject)
        buttons.addStretch(1)
        buttons.addWidget(self.parse_btn)
        buttons.addWidget(self.export_btn)
        buttons.addWidget(self.close_btn)
        layout.addLayout(buttons)

    def _browse(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Wybierz Rekordbox XML",
            "",
            "XML (*.xml)",
        )
        if path:
            self.input_path.setText(path)

    def _parse(self):
        path = Path(self.input_path.text().strip())
        if not path.exists():
            self.status.setText("Nie znaleziono pliku.")
            return
        self._tracks = parse_rekordbox_xml(path)
        self.status.setText(f"Wczytano utworów: {len(self._tracks)}")

    def _export(self):
        if not self._tracks:
            self._parse()
        if not self._tracks:
            return
        out_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Zapisz VirtualDJ XML",
            "",
            "XML (*.xml)",
        )
        if not out_path:
            return
        export_virtualdj_xml(self._tracks, Path(out_path))
        QtWidgets.QMessageBox.information(self, "Konwerter XML", "Eksport zakończony.")




