from __future__ import annotations

import csv
import shutil
from pathlib import Path

from PyQt6 import QtCore, QtGui, QtWidgets

from lumbago_app.core.models import DuplicateGroup, Track
from lumbago_app.core.audio import file_hash
from lumbago_app.core.services import DuplicateResult, find_duplicates_by_tags
from lumbago_app.data.repository import delete_tracks_by_paths


_BG = "#0a0d1a"
_CYAN = "#00d4ff"
_YELLOW = "#f59e0b"
_TEXT = "#e6f7ff"
_TEXT_DIM = "#94a3b8"
_CARD_BG = "#111827"
_BORDER = "#1e2d45"


def _format_size(size: int | None) -> str:
    if not size:
        return ""
    if size < 1024:
        return f"{size} B"
    if size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    return f"{size / (1024 * 1024):.1f} MB"


def _safe_size(path: str) -> int | None:
    try:
        return Path(path).stat().st_size
    except Exception:
        return None


class _ScanSignals(QtCore.QObject):
    progress = QtCore.pyqtSignal(int, int)
    finished = QtCore.pyqtSignal(object)


class _ScanWorker(QtCore.QRunnable):
    """Skanowanie duplikatow w tle."""

    def __init__(self, tracks: list[Track], method: str):
        super().__init__()
        self.tracks = tracks
        self.method = method
        self.signals = _ScanSignals()
        self._stop = False

    def stop(self):
        self._stop = True

    def run(self):
        result = self._scan()
        self.signals.finished.emit(result)

    def _scan(self) -> DuplicateResult:
        if self.method == "Tagi":
            return find_duplicates_by_tags(self.tracks)

        if self.method == "Hash":
            return self._scan_hash()

        # Fingerprint / Etapowo - fallback to hash
        return self._scan_hash()

    def _scan_hash(self) -> DuplicateResult:
        hash_groups: dict[str, list[int]] = {}
        total = len(self.tracks)
        for idx, track in enumerate(self.tracks, 1):
            if self._stop:
                break
            self.signals.progress.emit(idx, total)
            try:
                h = track.file_hash or file_hash(Path(track.path))
            except Exception:
                continue
            if h:
                hash_groups.setdefault(h, []).append(idx)

        groups = [
            DuplicateGroup(track_ids=ids, similarity=1.0)
            for ids in hash_groups.values()
            if len(ids) > 1
        ]
        return DuplicateResult(groups=groups)


class DuplicatesPage(QtWidgets.QWidget):
    """Inline strona duplikatow dla QStackedWidget."""

    tracks_deleted = QtCore.pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._tracks: list[Track] = []
        self._track_map: dict[str, Track] = {}
        self._groups: list[list[Track]] = []
        self._scanner: _ScanWorker | None = None
        self._build_ui()

    def set_tracks(self, tracks: list[Track]) -> None:
        """Ustaw utwory do analizy."""
        self._tracks = list(tracks)
        self._track_map = {t.path: t for t in tracks}
        self._groups = []
        self.tree.clear()
        self._update_summary(0, 0, 0)

    # ------------------------------------------------------------------ UI

    def _build_ui(self):
        self.setStyleSheet(f"""
            DuplicatesPage {{
                background-color: {_BG};
            }}
            QFrame#Card {{
                background-color: {_CARD_BG};
                border: 1px solid {_BORDER};
                border-radius: 10px;
            }}
            QLabel#SectionTitle {{
                color: {_TEXT};
                font-size: 15px;
                font-weight: 700;
            }}
            QLabel {{
                color: {_TEXT_DIM};
            }}
            QComboBox {{
                background-color: {_CARD_BG};
                color: {_TEXT};
                border: 1px solid {_BORDER};
                border-radius: 6px;
                padding: 4px 10px;
                min-width: 130px;
            }}
            QComboBox::drop-down {{
                border: none;
            }}
            QComboBox QAbstractItemView {{
                background-color: {_CARD_BG};
                color: {_TEXT};
                border: 1px solid {_BORDER};
                selection-background-color: {_CYAN};
                selection-color: {_BG};
            }}
            QPushButton {{
                background-color: {_CARD_BG};
                color: {_TEXT};
                border: 1px solid {_BORDER};
                border-radius: 8px;
                padding: 6px 16px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                border-color: {_CYAN};
            }}
            QPushButton#PrimaryAction {{
                background-color: {_CYAN};
                color: {_BG};
                border: none;
                font-weight: 700;
            }}
            QPushButton#PrimaryAction:hover {{
                background-color: #33ddff;
            }}
            QTreeWidget {{
                background-color: {_BG};
                color: {_TEXT};
                border: 1px solid {_BORDER};
                border-radius: 8px;
                alternate-background-color: #0f1225;
            }}
            QTreeWidget::item {{
                padding: 3px 0;
            }}
            QTreeWidget::item:selected {{
                background-color: rgba(0, 212, 255, 0.15);
            }}
            QHeaderView::section {{
                background-color: {_CARD_BG};
                color: {_TEXT_DIM};
                border: none;
                border-bottom: 1px solid {_BORDER};
                padding: 5px 8px;
                font-size: 11px;
            }}
        """)

        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        # -- top toolbar --
        toolbar_frame = QtWidgets.QFrame()
        toolbar_frame.setObjectName("Card")
        toolbar_lay = QtWidgets.QHBoxLayout(toolbar_frame)
        toolbar_lay.setContentsMargins(14, 10, 14, 10)
        toolbar_lay.setSpacing(10)

        title = QtWidgets.QLabel("Duplikaty")
        title.setObjectName("SectionTitle")
        toolbar_lay.addWidget(title)

        toolbar_lay.addSpacing(12)
        toolbar_lay.addWidget(QtWidgets.QLabel("Metoda:"))
        self.method_combo = QtWidgets.QComboBox()
        self.method_combo.addItems(["Hash", "Tagi", "Fingerprint", "Etapowo"])
        self.method_combo.setToolTip("Wybierz metode wykrywania duplikatow")
        toolbar_lay.addWidget(self.method_combo)

        self.scan_btn = QtWidgets.QPushButton("Szukaj duplikaty")
        self.scan_btn.setObjectName("PrimaryAction")
        self.scan_btn.setToolTip("Rozpocznij skanowanie")
        self.scan_btn.clicked.connect(self._run_scan)
        toolbar_lay.addWidget(self.scan_btn)

        self.progress_label = QtWidgets.QLabel("")
        self.progress_label.setStyleSheet(f"color: {_YELLOW}; font-size: 12px;")
        toolbar_lay.addWidget(self.progress_label)

        toolbar_lay.addStretch(1)
        root.addWidget(toolbar_frame)

        # -- main content: tree + summary --
        content = QtWidgets.QHBoxLayout()
        content.setSpacing(12)

        # tree
        self.tree = QtWidgets.QTreeWidget()
        self.tree.setColumnCount(7)
        self.tree.setHeaderLabels(
            ["Grupa", "Tytul", "Artysta", "Sciezka", "Rozmiar", "BPM", "Tonacja"]
        )
        self.tree.setRootIsDecorated(True)
        self.tree.setAlternatingRowColors(True)
        self.tree.setUniformRowHeights(True)
        header = self.tree.header()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.Interactive
        )
        self.tree.setSelectionMode(
            QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection
        )
        content.addWidget(self.tree, 1)

        # summary panel
        summary_frame = QtWidgets.QFrame()
        summary_frame.setObjectName("Card")
        summary_frame.setFixedWidth(200)
        summary_lay = QtWidgets.QVBoxLayout(summary_frame)
        summary_lay.setContentsMargins(16, 14, 16, 14)
        summary_lay.setSpacing(12)

        summary_title = QtWidgets.QLabel("Podsumowanie")
        summary_title.setObjectName("SectionTitle")
        summary_lay.addWidget(summary_title)

        self._stat_groups = self._make_stat_row(
            summary_lay, "Grup znalezionych", "0", _CYAN
        )
        self._stat_files = self._make_stat_row(
            summary_lay, "Plikow do usuniecia", "0", _YELLOW
        )
        self._stat_space = self._make_stat_row(
            summary_lay, "Miejsce do odzyskania", "0 B", _CYAN
        )

        summary_lay.addStretch(1)
        content.addWidget(summary_frame)

        root.addLayout(content, 1)

        # -- bottom action bar --
        action_frame = QtWidgets.QFrame()
        action_frame.setObjectName("Card")
        action_lay = QtWidgets.QHBoxLayout(action_frame)
        action_lay.setContentsMargins(14, 8, 14, 8)
        action_lay.setSpacing(10)

        self.keep_first_btn = QtWidgets.QPushButton("Zachowaj pierwszy")
        self.keep_first_btn.setToolTip(
            "Zaznacz wszystkie oprócz pierwszego w kazdej grupie"
        )
        self.keep_first_btn.clicked.connect(self._keep_first)
        action_lay.addWidget(self.keep_first_btn)

        self.delete_rest_btn = QtWidgets.QPushButton("Usun reszte")
        self.delete_rest_btn.setToolTip("Usun zaznaczone pliki z dysku i bazy")
        self.delete_rest_btn.clicked.connect(self._delete_checked)
        action_lay.addWidget(self.delete_rest_btn)

        action_lay.addStretch(1)

        self.export_csv_btn = QtWidgets.QPushButton("Eksport CSV")
        self.export_csv_btn.setToolTip("Zapisz raport duplikatow do pliku CSV")
        self.export_csv_btn.clicked.connect(self._export_csv)
        action_lay.addWidget(self.export_csv_btn)

        root.addWidget(action_frame)

    @staticmethod
    def _make_stat_row(
        parent_layout: QtWidgets.QVBoxLayout,
        label: str,
        value: str,
        color: str,
    ) -> QtWidgets.QLabel:
        val_lbl = QtWidgets.QLabel(value)
        val_lbl.setStyleSheet(
            f"color: {color}; font-size: 22px; font-weight: 700;"
        )
        desc_lbl = QtWidgets.QLabel(label)
        desc_lbl.setStyleSheet(f"color: {_TEXT_DIM}; font-size: 11px;")
        parent_layout.addWidget(val_lbl)
        parent_layout.addWidget(desc_lbl)
        return val_lbl

    # -------------------------------------------------------------- scan

    def _run_scan(self):
        if not self._tracks:
            return
        self.tree.clear()
        self._groups = []
        method = self.method_combo.currentText()
        self.scan_btn.setEnabled(False)
        self.progress_label.setText("Skanowanie...")

        self._scanner = _ScanWorker(self._tracks, method)
        self._scanner.signals.progress.connect(self._on_progress)
        self._scanner.signals.finished.connect(self._on_finished)
        QtCore.QThreadPool.globalInstance().start(self._scanner)

    def _on_progress(self, current: int, total: int):
        self.progress_label.setText(f"{current}/{total}")

    def _on_finished(self, result: DuplicateResult):
        self.scan_btn.setEnabled(True)
        self.progress_label.setText("")
        self._populate_tree(result)

    # --------------------------------------------------------- populate

    def _populate_tree(self, result: DuplicateResult):
        self.tree.clear()
        self._groups = []
        total_dup_files = 0
        total_dup_size = 0

        for group_idx, group in enumerate(result.groups, 1):
            tracks = [
                self._tracks[i - 1]
                for i in group.track_ids
                if 0 < i <= len(self._tracks)
            ]
            if len(tracks) < 2:
                continue
            self._groups.append(tracks)

            # confidence badge color
            sim = group.similarity
            if sim >= 0.95:
                badge_color = "#22c55e"
                badge_text = f"Pewnosc: {sim:.0%}"
            elif sim >= 0.8:
                badge_color = _YELLOW
                badge_text = f"Pewnosc: {sim:.0%}"
            else:
                badge_color = "#ef4444"
                badge_text = f"Pewnosc: {sim:.0%}"

            parent = QtWidgets.QTreeWidgetItem(
                [f"Grupa {group_idx}  [{badge_text}]"]
            )
            parent.setFirstColumnSpanned(True)
            parent.setForeground(0, QtGui.QColor(badge_color))
            font = parent.font(0)
            font.setBold(True)
            parent.setFont(0, font)
            self.tree.addTopLevelItem(parent)

            for t_idx, track in enumerate(tracks):
                size = track.file_size or _safe_size(track.path)
                child = QtWidgets.QTreeWidgetItem(
                    [
                        "",
                        track.title or "",
                        track.artist or "",
                        track.path,
                        _format_size(size),
                        str(track.bpm) if track.bpm else "",
                        track.key or "",
                    ]
                )
                child.setCheckState(0, QtCore.Qt.CheckState.Unchecked)
                child.setData(0, QtCore.Qt.ItemDataRole.UserRole, track.path)
                parent.addChild(child)

                # count duplicates (all except first)
                if t_idx > 0:
                    total_dup_files += 1
                    total_dup_size += size or 0

            parent.setExpanded(True)

        self._update_summary(
            len(self._groups), total_dup_files, total_dup_size
        )

    def _update_summary(
        self, groups: int, dup_files: int, dup_size: int
    ) -> None:
        self._stat_groups.setText(str(groups))
        self._stat_files.setText(str(dup_files))
        self._stat_space.setText(_format_size(dup_size) or "0 B")

    # --------------------------------------------------------- actions

    def _keep_first(self):
        """Zaznacz wszystkie oprócz pierwszego w kazdej grupie."""
        for i in range(self.tree.topLevelItemCount()):
            parent = self.tree.topLevelItem(i)
            for idx in range(parent.childCount()):
                state = (
                    QtCore.Qt.CheckState.Unchecked
                    if idx == 0
                    else QtCore.Qt.CheckState.Checked
                )
                parent.child(idx).setCheckState(0, state)

    def _checked_paths(self) -> list[str]:
        paths: list[str] = []
        for i in range(self.tree.topLevelItemCount()):
            parent = self.tree.topLevelItem(i)
            for idx in range(parent.childCount()):
                child = parent.child(idx)
                if child.checkState(0) == QtCore.Qt.CheckState.Checked:
                    path = child.data(0, QtCore.Qt.ItemDataRole.UserRole)
                    if path:
                        paths.append(path)
        return paths

    def _delete_checked(self):
        paths = self._checked_paths()
        if not paths:
            return
        confirm = QtWidgets.QMessageBox.question(
            self,
            "Potwierdzenie",
            f"Usunac {len(paths)} plik(ow) z dysku i bazy danych?",
        )
        if confirm != QtWidgets.QMessageBox.StandardButton.Yes:
            return

        trash_dir = Path(paths[0]).parent.parent / ".lumbago_trash"
        trash_dir.mkdir(parents=True, exist_ok=True)
        moved: list[str] = []
        for path in paths:
            src = Path(path)
            if not src.exists():
                moved.append(path)
                continue
            dst = trash_dir / src.name
            counter = 1
            while dst.exists():
                dst = trash_dir / f"{src.stem}_{counter}{src.suffix}"
                counter += 1
            try:
                shutil.move(str(src), str(dst))
                moved.append(path)
            except Exception:
                continue

        if moved:
            delete_tracks_by_paths(moved)
            # remove from tree
            for i in range(self.tree.topLevelItemCount() - 1, -1, -1):
                parent = self.tree.topLevelItem(i)
                for idx in range(parent.childCount() - 1, -1, -1):
                    child = parent.child(idx)
                    p = child.data(0, QtCore.Qt.ItemDataRole.UserRole)
                    if p in moved:
                        parent.removeChild(child)
                if parent.childCount() < 2:
                    self.tree.takeTopLevelItem(i)
            self.tracks_deleted.emit(moved)

    def _export_csv(self):
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Zapisz raport CSV",
            "",
            "CSV (*.csv)",
        )
        if not path:
            return
        with open(path, "w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(
                ["grupa", "tytul", "artysta", "sciezka", "rozmiar", "bpm", "tonacja"]
            )
            for i in range(self.tree.topLevelItemCount()):
                parent = self.tree.topLevelItem(i)
                for idx in range(parent.childCount()):
                    child = parent.child(idx)
                    writer.writerow(
                        [
                            parent.text(0),
                            child.text(1),
                            child.text(2),
                            child.text(3),
                            child.text(4),
                            child.text(5),
                            child.text(6),
                        ]
                    )
