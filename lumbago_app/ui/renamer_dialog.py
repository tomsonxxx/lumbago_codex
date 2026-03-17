from __future__ import annotations

from PyQt6 import QtCore, QtWidgets
from lumbago_app.ui.widgets import apply_dialog_fade, dialog_icon_pixmap

from lumbago_app.core.models import Track
from lumbago_app.core.renamer import apply_copy_plan, apply_rename_plan, build_rename_plan, undo_last_rename
from lumbago_app.data.repository import update_track_paths_bulk


_PRESETS = [
    ("{artist} - {title}", "Artysta - Tytuł"),
    ("{artist} - {album} - {title}", "Artysta - Album - Tytuł"),
    ("{bpm}_{key} - {artist} - {title}", "BPM_Tonacja - Artysta - Tytuł"),
    ("{year} - {artist} - {title}", "Rok - Artysta - Tytuł"),
    ("{title}", "Tylko tytuł"),
]


class RenamerDialog(QtWidgets.QDialog):
    def __init__(self, tracks: list[Track], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Renamer")
        self.setMinimumSize(900, 560)
        apply_dialog_fade(self)
        self._tracks = tracks
        self._plan = []
        self._build_ui()
        self._preview()

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

        # Presets
        preset_row = QtWidgets.QHBoxLayout()
        preset_row.addWidget(QtWidgets.QLabel("Szablon:"))
        self.preset_combo = QtWidgets.QComboBox()
        self.preset_combo.addItem("— wybierz szablon —", "")
        for pattern, label in _PRESETS:
            self.preset_combo.addItem(label, pattern)
        self.preset_combo.currentIndexChanged.connect(self._on_preset_changed)
        preset_row.addWidget(self.preset_combo, 1)
        layout.addLayout(preset_row)

        # Pattern input
        pattern_row = QtWidgets.QHBoxLayout()
        pattern_row.addWidget(QtWidgets.QLabel("Wzorzec:"))
        self.pattern = QtWidgets.QLineEdit("{artist} - {title}")
        self.pattern.setToolTip(
            "Dostępne zmienne: {artist} {title} {album} {genre} {bpm} {key} {year} {index}"
        )
        self.pattern.textChanged.connect(self._preview)
        pattern_row.addWidget(self.pattern, 1)
        layout.addLayout(pattern_row)

        # Variable buttons
        vars_row = QtWidgets.QHBoxLayout()
        vars_row.addWidget(QtWidgets.QLabel("Wstaw:"))
        for var in ["{artist}", "{title}", "{album}", "{genre}", "{bpm}", "{key}", "{year}"]:
            btn = QtWidgets.QPushButton(var)
            btn.setFixedHeight(24)
            btn.setMaximumWidth(80)
            btn.clicked.connect(lambda _, v=var: self._insert_variable(v))
            vars_row.addWidget(btn)
        vars_row.addStretch(1)
        layout.addLayout(vars_row)

        # Options row: case + copy mode
        opts_row = QtWidgets.QHBoxLayout()
        opts_row.addWidget(QtWidgets.QLabel("Wielkość liter:"))
        self.case_combo = QtWidgets.QComboBox()
        self.case_combo.addItems(["Bez zmian", "UPPERCASE", "lowercase", "Title Case"])
        self.case_combo.setFixedWidth(130)
        self.case_combo.currentIndexChanged.connect(self._preview)
        opts_row.addWidget(self.case_combo)
        opts_row.addSpacing(20)
        self.copy_check = QtWidgets.QCheckBox("Kopiuj zamiast przenoś (tryb bezpieczny)")
        self.copy_check.setToolTip(
            "Gdy zaznaczone, pliki zostaną skopiowane do nowej nazwy.\n"
            "Oryginały pozostają bez zmian. Ścieżki w bibliotece NIE są aktualizowane."
        )
        self.copy_check.stateChanged.connect(lambda _: self._update_status_note())
        opts_row.addWidget(self.copy_check)
        opts_row.addStretch(1)
        layout.addLayout(opts_row)

        self.table = QtWidgets.QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Stara nazwa", "Nowa nazwa", "Status"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(
            0, QtWidgets.QHeaderView.ResizeMode.Interactive
        )
        self.table.horizontalHeader().setSectionResizeMode(
            1, QtWidgets.QHeaderView.ResizeMode.Interactive
        )
        layout.addWidget(self.table, 1)

        self.status_label = QtWidgets.QLabel("")
        layout.addWidget(self.status_label)

        actions = QtWidgets.QHBoxLayout()
        self.apply_btn = QtWidgets.QPushButton("Zastosuj")
        self.apply_btn.setToolTip("Zmień nazwy plików według planu")
        self.apply_btn.clicked.connect(self._apply)
        self.undo_btn = QtWidgets.QPushButton("Cofnij ostatnią zmianę")
        self.undo_btn.setToolTip("Przywróć poprzednie nazwy z ostatniego użycia")
        self.undo_btn.clicked.connect(self._undo)
        self.close_btn = QtWidgets.QPushButton("Zamknij")
        self.close_btn.clicked.connect(self.reject)
        actions.addStretch(1)
        actions.addWidget(self.apply_btn)
        actions.addWidget(self.undo_btn)
        actions.addWidget(self.close_btn)
        layout.addLayout(actions)

    def _on_preset_changed(self, idx: int):
        pattern = self.preset_combo.itemData(idx)
        if pattern:
            self.pattern.setText(pattern)

    def _insert_variable(self, var: str):
        pos = self.pattern.cursorPosition()
        text = self.pattern.text()
        self.pattern.setText(text[:pos] + var + text[pos:])
        self.pattern.setCursorPosition(pos + len(var))

    def _apply_case(self, name: str) -> str:
        case_idx = self.case_combo.currentIndex()
        if case_idx == 1:
            return name.upper()
        if case_idx == 2:
            return name.lower()
        if case_idx == 3:
            return name.title()
        return name

    def _preview(self):
        self._plan = build_rename_plan(self._tracks, self.pattern.text().strip())
        # Zastosuj transformację wielkości liter do nowych ścieżek
        from pathlib import Path as _Path
        for item in self._plan:
            if not item.conflict:
                stem = self._apply_case(item.new_path.stem)
                item.new_path = item.new_path.with_name(stem + item.new_path.suffix)
        self.table.setRowCount(0)
        ok_count = 0
        conflict_count = 0
        for item in self._plan:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QtWidgets.QTableWidgetItem(item.old_path.name))
            self.table.setItem(row, 1, QtWidgets.QTableWidgetItem(item.new_path.name))
            if item.conflict:
                status = f"Konflikt: {item.reason}"
                status_item = QtWidgets.QTableWidgetItem(status)
                status_item.setForeground(QtCore.Qt.GlobalColor.red)
                conflict_count += 1
            else:
                status_item = QtWidgets.QTableWidgetItem("OK")
                status_item.setForeground(QtCore.Qt.GlobalColor.green)
                ok_count += 1
            self.table.setItem(row, 2, status_item)
        copy_note = " [TRYB KOPIOWANIA]" if self.copy_check.isChecked() else ""
        self.status_label.setText(
            f"Razem: {len(self._plan)} | OK: {ok_count} | Konflikty: {conflict_count}{copy_note}"
        )
        self.apply_btn.setEnabled(ok_count > 0)

    def _apply(self):
        if not self._plan:
            self._preview()
        if self.copy_check.isChecked():
            copied = apply_copy_plan(self._plan)
            QtWidgets.QMessageBox.information(
                self, "Kopiowanie zakończone",
                f"Skopiowano {copied} plików.\n"
                "Oryginalne pliki oraz ścieżki w bibliotece pozostają bez zmian."
            )
            self.reject()
            return
        history = apply_rename_plan(self._plan)
        update_track_paths_bulk(history)
        self.accept()

    def _update_status_note(self):
        current = self.status_label.text()
        base = current.replace(" [TRYB KOPIOWANIA]", "")
        if self.copy_check.isChecked():
            self.status_label.setText(base + " [TRYB KOPIOWANIA]")
        else:
            self.status_label.setText(base)

    def _undo(self):
        history = undo_last_rename()
        flipped = [{"old": item["new"], "new": item["old"]} for item in history]
        update_track_paths_bulk(flipped)
        self.accept()
