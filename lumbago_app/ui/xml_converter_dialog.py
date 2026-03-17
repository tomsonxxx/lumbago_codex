from __future__ import annotations

from pathlib import Path

from PyQt6 import QtWidgets, QtGui
from lumbago_app.ui.widgets import apply_dialog_fade, dialog_icon_pixmap

from lumbago_app.services.xml_converter import (
    export_rekordbox_xml,
    export_traktor_nml,
    export_virtualdj_xml,
    parse_rekordbox_xml,
    parse_traktor_nml,
    parse_virtualdj_xml,
)


class XmlConverterDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Konwerter XML / NML")
        self.setMinimumSize(780, 460)
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

        # Wybór formatu wejściowego
        fmt_row = QtWidgets.QHBoxLayout()
        fmt_row.addWidget(QtWidgets.QLabel("Format wejściowy:"))
        self.format_combo = QtWidgets.QComboBox()
        self.format_combo.addItems(["Rekordbox XML", "VirtualDJ XML", "Traktor NML"])
        fmt_row.addWidget(self.format_combo)
        fmt_row.addStretch(1)
        layout.addLayout(fmt_row)

        # Ścieżka pliku
        row = QtWidgets.QHBoxLayout()
        self.input_path = QtWidgets.QLineEdit()
        self.input_path.setPlaceholderText("Wybierz plik wejściowy")
        row.addWidget(self.input_path, 1)
        browse_btn = QtWidgets.QPushButton("Wybierz")
        browse_btn.clicked.connect(self._browse)
        row.addWidget(browse_btn)
        layout.addLayout(row)

        self.status = QtWidgets.QLabel("Brak pliku")
        self.status.setObjectName("DialogHint")
        layout.addWidget(self.status)

        # Podgląd — tabela
        self.preview_table = QtWidgets.QTableWidget(0, 5)
        self.preview_table.setHorizontalHeaderLabels(["Tytuł", "Artysta", "BPM", "Tonacja", "Gatunek"])
        self.preview_table.horizontalHeader().setStretchLastSection(True)
        self.preview_table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.preview_table.setAlternatingRowColors(True)
        layout.addWidget(self.preview_table, 1)

        buttons = QtWidgets.QHBoxLayout()
        self.parse_btn = QtWidgets.QPushButton("Wczytaj i podgląd")
        self.parse_btn.clicked.connect(self._parse)

        self.export_vdj_btn = QtWidgets.QPushButton("→ VirtualDJ XML")
        self.export_vdj_btn.setToolTip("Eksportuj do VirtualDJ XML z hot cues")
        self.export_vdj_btn.clicked.connect(lambda: self._export("virtualdj"))

        self.export_rbx_btn = QtWidgets.QPushButton("→ Rekordbox XML")
        self.export_rbx_btn.setToolTip("Eksportuj do Rekordbox XML z POSITION_MARK")
        self.export_rbx_btn.clicked.connect(lambda: self._export("rekordbox"))

        self.export_nml_btn = QtWidgets.QPushButton("→ Traktor NML")
        self.export_nml_btn.setToolTip("Eksportuj do Traktor NML z hot cues")
        self.export_nml_btn.clicked.connect(lambda: self._export("traktor"))

        self.close_btn = QtWidgets.QPushButton("Zamknij")
        self.close_btn.clicked.connect(self.reject)

        buttons.addWidget(self.parse_btn)
        buttons.addStretch(1)
        buttons.addWidget(self.export_vdj_btn)
        buttons.addWidget(self.export_rbx_btn)
        buttons.addWidget(self.export_nml_btn)
        buttons.addWidget(self.close_btn)
        layout.addLayout(buttons)

    def _browse(self):
        fmt = self.format_combo.currentText()
        if "NML" in fmt:
            filt = "Traktor NML (*.nml)"
        else:
            filt = "XML (*.xml)"
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Wybierz plik", "", filt)
        if path:
            self.input_path.setText(path)

    def _parse(self):
        path = Path(self.input_path.text().strip())
        if not path.exists():
            self.status.setText("Nie znaleziono pliku.")
            return
        fmt = self.format_combo.currentText()
        try:
            if "Traktor" in fmt:
                self._tracks = parse_traktor_nml(path)
            elif "VirtualDJ" in fmt:
                self._tracks = parse_virtualdj_xml(path)
            else:
                self._tracks = parse_rekordbox_xml(path)
        except Exception as exc:
            self.status.setText(f"Błąd parsowania: {exc}")
            return

        cue_count = sum(1 for t in self._tracks if t.hot_cues)
        self.status.setText(
            f"Wczytano: {len(self._tracks)} utworów"
            + (f" • {cue_count} z hot cues" if cue_count else "")
        )
        self._fill_preview()

    def _fill_preview(self):
        self.preview_table.setRowCount(0)
        for item in self._tracks:
            row = self.preview_table.rowCount()
            self.preview_table.insertRow(row)
            self.preview_table.setItem(row, 0, QtWidgets.QTableWidgetItem(item.title or ""))
            self.preview_table.setItem(row, 1, QtWidgets.QTableWidgetItem(item.artist or ""))
            self.preview_table.setItem(row, 2, QtWidgets.QTableWidgetItem(item.bpm or ""))
            self.preview_table.setItem(row, 3, QtWidgets.QTableWidgetItem(item.key or ""))
            self.preview_table.setItem(row, 4, QtWidgets.QTableWidgetItem(item.genre or ""))

    def _export(self, target: str):
        if not self._tracks:
            self._parse()
        if not self._tracks:
            return
        filters = {
            "virtualdj": ("VirtualDJ XML", "XML (*.xml)"),
            "rekordbox": ("Rekordbox XML", "XML (*.xml)"),
            "traktor": ("Traktor NML", "NML (*.nml)"),
        }
        label, filt = filters[target]
        out_path, _ = QtWidgets.QFileDialog.getSaveFileName(self, f"Zapisz {label}", "", filt)
        if not out_path:
            return
        out = Path(out_path)
        if target == "virtualdj":
            export_virtualdj_xml(self._tracks, out)
        elif target == "rekordbox":
            export_rekordbox_xml(self._tracks, out)
        else:
            export_traktor_nml(self._tracks, out)
        QtWidgets.QMessageBox.information(self, "Konwerter", f"Eksport do {label} zakończony.\n{out_path}")
