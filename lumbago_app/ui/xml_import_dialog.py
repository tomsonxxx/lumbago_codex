from __future__ import annotations

from pathlib import Path

from PyQt6 import QtWidgets

from lumbago_app.core.models import Track
from lumbago_app.data.repository import upsert_tracks
from lumbago_app.services.xml_converter import parse_rekordbox_xml, parse_virtualdj_xml


class XmlImportDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Import XML")
        self.setMinimumSize(720, 420)
        self._tracks: list[Track] = []
        self._build_ui()

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        row = QtWidgets.QHBoxLayout()
        self.input_path = QtWidgets.QLineEdit()
        self.input_path.setPlaceholderText("Wybierz plik Rekordbox lub VirtualDJ XML")
        row.addWidget(self.input_path, 1)
        browse_btn = QtWidgets.QPushButton("Wybierz")
        browse_btn.clicked.connect(self._browse)
        row.addWidget(browse_btn)
        layout.addLayout(row)

        self.status = QtWidgets.QLabel("Brak pliku")
        layout.addWidget(self.status)

        buttons = QtWidgets.QHBoxLayout()
        self.parse_btn = QtWidgets.QPushButton("Wczytaj")
        self.parse_btn.clicked.connect(self._parse)
        self.import_btn = QtWidgets.QPushButton("Importuj do bazy")
        self.import_btn.clicked.connect(self._import)
        self.close_btn = QtWidgets.QPushButton("Zamknij")
        self.close_btn.clicked.connect(self.reject)
        buttons.addStretch(1)
        buttons.addWidget(self.parse_btn)
        buttons.addWidget(self.import_btn)
        buttons.addWidget(self.close_btn)
        layout.addLayout(buttons)

    def _browse(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Wybierz XML",
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
        tracks = []
        try:
            tracks = parse_rekordbox_xml(path)
        except Exception:
            tracks = []
        if not tracks:
            try:
                tracks = parse_virtualdj_xml(path)
            except Exception:
                tracks = []
        self._tracks = [
            Track(
                path=t.path,
                title=t.title,
                artist=t.artist,
                album=t.album,
                genre=t.genre,
                bpm=float(t.bpm) if t.bpm else None,
                key=t.key,
            )
            for t in tracks
            if t.path
        ]
        self.status.setText(f"Wczytano utworów: {len(self._tracks)}")

    def _import(self):
        if not self._tracks:
            self._parse()
        if not self._tracks:
            return
        upsert_tracks(self._tracks)
        QtWidgets.QMessageBox.information(self, "Import XML", f"Zaimportowano {len(self._tracks)} utworów.")
        self.accept()
