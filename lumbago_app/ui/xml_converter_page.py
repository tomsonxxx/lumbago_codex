"""Strona konwertera XML — widget inline do QStackedWidget."""
from __future__ import annotations

from pathlib import Path

from PyQt6 import QtCore, QtWidgets

from lumbago_app.core.models import Track
from lumbago_app.services.xml_converter import (
    XmlTrack,
    export_rekordbox_xml,
    export_traktor_nml,
    export_virtualdj_xml,
    parse_rekordbox_xml,
    parse_traktor_nml,
    parse_virtualdj_xml,
)

_PARSERS = {
    "Rekordbox XML": (parse_rekordbox_xml, "XML (*.xml)"),
    "VirtualDJ XML": (parse_virtualdj_xml, "XML (*.xml)"),
    "Traktor NML": (parse_traktor_nml, "NML (*.nml)"),
}

_EXPORTERS = {
    "VirtualDJ XML": (export_virtualdj_xml, "XML (*.xml)"),
    "Rekordbox XML": (export_rekordbox_xml, "XML (*.xml)"),
    "Traktor NML": (export_traktor_nml, "NML (*.nml)"),
}


class XmlConverterPage(QtWidgets.QWidget):
    """Inline XML Converter page widget for a QStackedWidget."""

    tracks_imported = QtCore.pyqtSignal(list)

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self._tracks: list[Track] = []
        self._imported_tracks: list[XmlTrack] = []
        self._build_ui()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_tracks(self, tracks: list[Track]) -> None:
        """Ustaw listę utworów dostępnych do eksportu."""
        self._tracks = list(tracks)
        self._export_count_lbl.setText(f"{len(self._tracks)} utworów w bibliotece")

    def set_track_count(self, count: int) -> None:
        """Zaktualizuj etykietę z liczbą utworów."""
        self._export_count_lbl.setText(f"{count} utworów w bibliotece")

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        root = QtWidgets.QHBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(20)

        root.addWidget(self._build_import_card(), 1)
        root.addWidget(self._build_export_card(), 1)

    # -- Import card ---------------------------------------------------

    def _build_import_card(self) -> QtWidgets.QFrame:
        card = QtWidgets.QFrame()
        card.setObjectName("Card")
        lay = QtWidgets.QVBoxLayout(card)
        lay.setContentsMargins(20, 18, 20, 20)
        lay.setSpacing(12)

        title = QtWidgets.QLabel("\U0001f4e5 Import XML")
        title.setObjectName("SectionTitle")
        lay.addWidget(title)

        # Format selector
        fmt_row = QtWidgets.QHBoxLayout()
        fmt_row.addWidget(self._label("Format:"))
        self._import_format = QtWidgets.QComboBox()
        self._import_format.addItems(list(_PARSERS.keys()))
        fmt_row.addWidget(self._import_format, 1)
        lay.addLayout(fmt_row)

        # File path
        path_row = QtWidgets.QHBoxLayout()
        self._import_path = QtWidgets.QLineEdit()
        self._import_path.setPlaceholderText("Ścieżka do pliku XML / NML…")
        path_row.addWidget(self._import_path, 1)
        browse_btn = QtWidgets.QPushButton("Przeglądaj")
        browse_btn.clicked.connect(self._browse_import)
        path_row.addWidget(browse_btn)
        lay.addLayout(path_row)

        # Import button
        import_btn = QtWidgets.QPushButton("Importuj")
        import_btn.setObjectName("PrimaryAction")
        import_btn.clicked.connect(self._do_import)
        lay.addWidget(import_btn)

        # Results table
        self._import_table = QtWidgets.QTableWidget(0, 4)
        self._import_table.setHorizontalHeaderLabels(
            ["Tytuł", "Artysta", "BPM", "Tonacja"]
        )
        self._import_table.horizontalHeader().setStretchLastSection(True)
        self._import_table.setEditTriggers(
            QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self._import_table.setAlternatingRowColors(True)
        lay.addWidget(self._import_table, 1)

        # Status
        self._import_status = QtWidgets.QLabel("Brak pliku")
        self._import_status.setStyleSheet("color: #94a3b8; font-size: 12px;")
        lay.addWidget(self._import_status)

        return card

    # -- Export card ----------------------------------------------------

    def _build_export_card(self) -> QtWidgets.QFrame:
        card = QtWidgets.QFrame()
        card.setObjectName("Card")
        lay = QtWidgets.QVBoxLayout(card)
        lay.setContentsMargins(20, 18, 20, 20)
        lay.setSpacing(12)

        title = QtWidgets.QLabel("\U0001f4e4 Export XML")
        title.setObjectName("SectionTitle")
        lay.addWidget(title)

        # Format selector
        fmt_row = QtWidgets.QHBoxLayout()
        fmt_row.addWidget(self._label("Format:"))
        self._export_format = QtWidgets.QComboBox()
        self._export_format.addItems(list(_EXPORTERS.keys()))
        fmt_row.addWidget(self._export_format, 1)
        lay.addLayout(fmt_row)

        # Track count
        self._export_count_lbl = QtWidgets.QLabel("0 utworów w bibliotece")
        self._export_count_lbl.setStyleSheet(
            "color: #94a3b8; font-size: 12px; padding: 2px 0;"
        )
        lay.addWidget(self._export_count_lbl)

        # Output path
        path_row = QtWidgets.QHBoxLayout()
        self._export_path = QtWidgets.QLineEdit()
        self._export_path.setPlaceholderText("Ścieżka zapisu pliku…")
        path_row.addWidget(self._export_path, 1)
        browse_btn = QtWidgets.QPushButton("Przeglądaj")
        browse_btn.clicked.connect(self._browse_export)
        path_row.addWidget(browse_btn)
        lay.addLayout(path_row)

        # Export button
        export_btn = QtWidgets.QPushButton("Eksportuj")
        export_btn.setObjectName("PrimaryAction")
        export_btn.clicked.connect(self._do_export)
        lay.addWidget(export_btn)

        lay.addStretch(1)

        # Status
        self._export_status = QtWidgets.QLabel("")
        self._export_status.setStyleSheet("color: #94a3b8; font-size: 12px;")
        lay.addWidget(self._export_status)

        return card

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _label(text: str) -> QtWidgets.QLabel:
        lbl = QtWidgets.QLabel(text)
        lbl.setStyleSheet("color: #e6f7ff; font-size: 13px;")
        return lbl

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _browse_import(self) -> None:
        fmt = self._import_format.currentText()
        _, filt = _PARSERS[fmt]
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Wybierz plik wejściowy", "", filt
        )
        if path:
            self._import_path.setText(path)

    def _browse_export(self) -> None:
        fmt = self._export_format.currentText()
        _, filt = _EXPORTERS[fmt]
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Zapisz plik", "", filt
        )
        if path:
            self._export_path.setText(path)

    def _do_import(self) -> None:
        raw = self._import_path.text().strip()
        if not raw:
            self._import_status.setText("Nie wybrano pliku.")
            return
        path = Path(raw)
        if not path.exists():
            self._import_status.setText("Plik nie istnieje.")
            return

        fmt = self._import_format.currentText()
        parser, _ = _PARSERS[fmt]
        try:
            self._imported_tracks = parser(path)
        except Exception as exc:
            self._import_status.setText(f"Błąd parsowania: {exc}")
            return

        count = len(self._imported_tracks)
        cue_count = sum(1 for t in self._imported_tracks if t.hot_cues)
        status = f"Zaimportowano {count} utworów"
        if cue_count:
            status += f" \u2022 {cue_count} z hot cues"
        self._import_status.setText(status)

        # Fill table
        self._import_table.setRowCount(0)
        for item in self._imported_tracks:
            row = self._import_table.rowCount()
            self._import_table.insertRow(row)
            self._import_table.setItem(
                row, 0, QtWidgets.QTableWidgetItem(item.title or "")
            )
            self._import_table.setItem(
                row, 1, QtWidgets.QTableWidgetItem(item.artist or "")
            )
            self._import_table.setItem(
                row, 2, QtWidgets.QTableWidgetItem(item.bpm or "")
            )
            self._import_table.setItem(
                row, 3, QtWidgets.QTableWidgetItem(item.key or "")
            )

        # Emit signal with dicts
        result = [
            {
                "path": t.path,
                "title": t.title,
                "artist": t.artist,
                "album": t.album,
                "genre": t.genre,
                "bpm": t.bpm,
                "key": t.key,
                "hot_cues": t.hot_cues,
            }
            for t in self._imported_tracks
        ]
        self.tracks_imported.emit(result)

    def _do_export(self) -> None:
        if not self._tracks:
            self._export_status.setText("Brak utworów do eksportu.")
            return

        raw = self._export_path.text().strip()
        if not raw:
            self._export_status.setText("Nie wybrano ścieżki zapisu.")
            return

        fmt = self._export_format.currentText()
        exporter, _ = _EXPORTERS[fmt]
        out = Path(raw)

        xml_tracks = [
            XmlTrack(
                path=t.path,
                title=t.title,
                artist=t.artist,
                album=t.album,
                genre=t.genre,
                bpm=str(t.bpm) if t.bpm is not None else None,
                key=t.key,
            )
            for t in self._tracks
        ]

        try:
            exporter(xml_tracks, out)
        except Exception as exc:
            self._export_status.setText(f"Błąd eksportu: {exc}")
            return

        self._export_status.setText(
            f"Wyeksportowano {len(xml_tracks)} utworów do {out.name}"
        )
