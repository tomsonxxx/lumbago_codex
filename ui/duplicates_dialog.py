from __future__ import annotations

import csv
import shutil
from pathlib import Path

from PyQt6 import QtCore, QtWidgets
from ui.widgets import apply_dialog_fade, dialog_icon_pixmap

from core.models import DuplicateGroup, Track
from core.audio import file_hash
from core.services import DuplicateResult, find_duplicates_by_tags
from data.repository import (
    delete_tracks_by_paths,
    update_track,
    update_track_paths_bulk,
    update_tracks_file_meta,
)
from services.recognizer import AcoustIdRecognizer


class DuplicatesDialog(QtWidgets.QDialog):
    def __init__(self, tracks: list[Track], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Duplikaty")
        self.setMinimumSize(900, 520)
        apply_dialog_fade(self)
        self._tracks = tracks
        self._track_map = {track.path: track for track in tracks}
        self._scanner = None
        self._groups: list[list[Track]] = []
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

        top = QtWidgets.QHBoxLayout()
        top.addWidget(QtWidgets.QLabel("Metoda wykrywania:"))
        self.method = QtWidgets.QComboBox()
        self.method.addItems(["Hash", "Tagi", "Fingerprint", "Etapowo", "Fuzzy"])
        self.method.setToolTip("Wybierz metodę wykrywania duplikatów")
        top.addWidget(self.method)
        self.run_btn = QtWidgets.QPushButton("Szukaj")
        self.run_btn.setToolTip("Uruchom skan duplikatów")
        self.run_btn.clicked.connect(self._run_scan)
        top.addWidget(self.run_btn)
        top.addStretch(1)
        layout.addLayout(top)

        self.tree = QtWidgets.QTreeWidget()
        self.tree.setColumnCount(7)
        self.tree.setHeaderLabels(
            ["Grupa", "Tytuł", "Artysta", "Ścieżka", "Rozmiar", "BPM", "Tonacja"]
        )
        self.tree.setRootIsDecorated(True)
        self.tree.setAlternatingRowColors(True)
        self.tree.setUniformRowHeights(True)
        header = self.tree.header()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Interactive)
        header.setSectionsMovable(True)
        header.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        header.customContextMenuRequested.connect(self._show_column_menu)
        layout.addWidget(self.tree, 1)

        actions = QtWidgets.QHBoxLayout()
        self.mark_btn = QtWidgets.QPushButton("Zaznacz duplikaty")
        self.mark_btn.setToolTip("Zaznacz wszystkie duplikaty (zostaw pierwsze)")
        self.mark_btn.clicked.connect(self._mark_duplicates)
        self.clear_btn = QtWidgets.QPushButton("Wyczyść zaznaczenie")
        self.clear_btn.setToolTip("Odznacz wszystkie pozycje")
        self.clear_btn.clicked.connect(self._clear_marks)
        self.move_btn = QtWidgets.QPushButton("Przenieś zaznaczone")
        self.move_btn.setToolTip("Przenieś zaznaczone pliki do folderu")
        self.move_btn.clicked.connect(self._move_selected)
        self.merge_btn = QtWidgets.QPushButton("Scal metadane")
        self.merge_btn.setToolTip("Scal brakujące tagi do pierwszego utworu w grupie")
        self.merge_btn.clicked.connect(self._merge_selected)
        self.delete_btn = QtWidgets.QPushButton("Usuń zaznaczone")
        self.delete_btn.setToolTip("Usuń zaznaczone pliki z dysku i bazy")
        self.delete_btn.clicked.connect(self._delete_selected)
        self.export_btn = QtWidgets.QPushButton("Eksportuj raport")
        self.export_btn.setToolTip("Zapisz raport CSV z wynikami")
        self.export_btn.clicked.connect(self._export_report)
        self.close_btn = QtWidgets.QPushButton("Zamknij")
        self.close_btn.clicked.connect(self.reject)
        actions.addWidget(self.mark_btn)
        actions.addWidget(self.clear_btn)
        actions.addStretch(1)
        actions.addWidget(self.move_btn)
        actions.addWidget(self.merge_btn)
        actions.addWidget(self.delete_btn)
        actions.addWidget(self.export_btn)
        actions.addWidget(self.close_btn)
        layout.addLayout(actions)

    def _run_scan(self):
        self.tree.clear()
        method = self.method.currentText()

        if method == "Fuzzy":
            from services.fuzzy_dedup import FuzzyDedupService
            progress = QtWidgets.QProgressDialog("Skanowanie duplikatów (fuzzy)...", None, 0, 1, self)
            progress.setWindowTitle("Duplikaty")
            progress.setMinimumDuration(0)
            progress.setValue(0)
            QtWidgets.QApplication.processEvents()
            svc = FuzzyDedupService()
            groups = svc.find_fuzzy_duplicates(self._tracks)
            result = [g.tracks for g in groups if len(g.tracks) > 1]
            progress.setValue(1)
            progress.close()
            self._populate_tree_flat(result)
            return

        progress = QtWidgets.QProgressDialog("Skanowanie duplikatów...", "Anuluj", 0, len(self._tracks), self)
        progress.setWindowTitle("Duplikaty")
        progress.setMinimumDuration(0)

        self._scanner = DuplicateScanWorker(self._tracks, method)

        def on_progress(current: int, total: int):
            progress.setMaximum(total)
            progress.setValue(current)
            if progress.wasCanceled():
                self._scanner.stop()

        def on_finished(result):
            progress.close()
            self._populate_tree(result)

        self._scanner.signals.progress.connect(on_progress)
        self._scanner.signals.finished.connect(on_finished)
        QtCore.QThreadPool.globalInstance().start(self._scanner)

    def _show_column_menu(self, pos):
        menu = QtWidgets.QMenu(self)
        show_all = menu.addAction("Pokaż wszystkie")
        hide_all = menu.addAction("Ukryj wszystkie")
        menu.addSeparator()
        actions = []
        for col in range(self.tree.columnCount()):
            name = self.tree.headerItem().text(col)
            action = QtWidgets.QAction(name, menu)
            action.setCheckable(True)
            action.setChecked(not self.tree.isColumnHidden(col))
            actions.append((action, col))
            menu.addAction(action)
        chosen = menu.exec(self.tree.header().mapToGlobal(pos))
        if chosen == show_all:
            for _, col in actions:
                self.tree.setColumnHidden(col, False)
            return
        if chosen == hide_all:
            self._hide_all_but_anchor([col for _, col in actions])
            return
        for action, col in actions:
            if chosen == action:
                if action.isChecked():
                    self.tree.setColumnHidden(col, False)
                else:
                    visible = sum(1 for _, c in actions if not self.tree.isColumnHidden(c))
                    if visible > 1:
                        self.tree.setColumnHidden(col, True)
                    else:
                        action.setChecked(True)
                break

    def _hide_all_but_anchor(self, columns: list[int]) -> None:
        if not columns:
            return
        anchor = columns[0]
        for col in columns:
            self.tree.setColumnHidden(col, col != anchor)

    def _populate_tree(self, result):
        self._groups = []
        for group_idx, group in enumerate(result.groups, 1):
            tracks = [self._tracks[i - 1] for i in group.track_ids if 0 < i <= len(self._tracks)]
            if len(tracks) < 2:
                continue
            self._groups.append(tracks)
            parent = QtWidgets.QTreeWidgetItem([f"Grupa {group_idx} (sim {group.similarity:.2f})"])
            parent.setFirstColumnSpanned(True)
            self.tree.addTopLevelItem(parent)
            for track in tracks:
                size = track.file_size or _safe_size(track.path)
                item = QtWidgets.QTreeWidgetItem(
                    [
                        "",
                        track.title or "",
                        track.artist or "",
                        track.path,
                        f"{size or ''}",
                        f"{track.bpm or ''}",
                        track.key or "",
                    ]
                )
                item.setCheckState(0, QtCore.Qt.CheckState.Unchecked)
                item.setData(0, QtCore.Qt.ItemDataRole.UserRole, track.path)
                parent.addChild(item)
            parent.setExpanded(True)

    def _populate_tree_flat(self, groups: list[list]):
        """Populate tree from a flat list of track groups (used by Fuzzy mode)."""
        self._groups = []
        for group_idx, tracks in enumerate(groups, 1):
            if len(tracks) < 2:
                continue
            self._groups.append(tracks)
            parent = QtWidgets.QTreeWidgetItem([f"Grupa {group_idx}"])
            parent.setFirstColumnSpanned(True)
            self.tree.addTopLevelItem(parent)
            for track in tracks:
                size = track.file_size or _safe_size(track.path)
                item = QtWidgets.QTreeWidgetItem(
                    [
                        "",
                        track.title or "",
                        track.artist or "",
                        track.path,
                        f"{size or ''}",
                        f"{track.bpm or ''}",
                        track.key or "",
                    ]
                )
                item.setCheckState(0, QtCore.Qt.CheckState.Unchecked)
                item.setData(0, QtCore.Qt.ItemDataRole.UserRole, track.path)
                parent.addChild(item)
            parent.setExpanded(True)

    def _mark_duplicates(self):
        for i in range(self.tree.topLevelItemCount()):
            parent = self.tree.topLevelItem(i)
            if parent.childCount() <= 1:
                continue
            parent.child(0).setCheckState(0, QtCore.Qt.CheckState.Unchecked)
            for idx in range(1, parent.childCount()):
                parent.child(idx).setCheckState(0, QtCore.Qt.CheckState.Checked)

    def _clear_marks(self):
        for i in range(self.tree.topLevelItemCount()):
            parent = self.tree.topLevelItem(i)
            for idx in range(parent.childCount()):
                parent.child(idx).setCheckState(0, QtCore.Qt.CheckState.Unchecked)

    def _selected_paths(self) -> list[str]:
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

    def _move_selected(self):
        paths = self._selected_paths()
        if not paths:
            return
        target_dir = QtWidgets.QFileDialog.getExistingDirectory(self, "Wybierz folder docelowy")
        if not target_dir:
            return
        history: list[dict[str, str]] = []
        for path in paths:
            src = Path(path)
            if not src.exists():
                continue
            dest = Path(target_dir) / src.name
            if dest.exists():
                dest = Path(target_dir) / f"dup_{src.name}"
            shutil.move(str(src), str(dest))
            history.append({"old": str(src), "new": str(dest)})
        if history:
            update_track_paths_bulk(history)
            self.accept()

    def _delete_selected(self):
        paths = self._selected_paths()
        if not paths:
            return
        confirm = QtWidgets.QMessageBox.question(
            self,
            "Potwierdzenie",
            "Czy na pewno usunąć zaznaczone pliki z dysku i bazy?",
        )
        if confirm != QtWidgets.QMessageBox.StandardButton.Yes:
            return
        for path in paths:
            try:
                Path(path).unlink(missing_ok=True)
            except Exception:
                continue
        delete_tracks_by_paths(paths)
        self.accept()

    def _export_report(self):
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
            writer.writerow(["group", "title", "artist", "path", "size", "bpm", "key"])
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

    def _merge_selected(self):
        changed = False
        for i in range(self.tree.topLevelItemCount()):
            parent = self.tree.topLevelItem(i)
            if parent.childCount() < 2:
                continue
            master_item = parent.child(0)
            master_path = master_item.data(0, QtCore.Qt.ItemDataRole.UserRole)
            if not master_path:
                continue
            master_track = self._track_map.get(master_path)
            if not master_track:
                continue
            for idx in range(1, parent.childCount()):
                child = parent.child(idx)
                if child.checkState(0) != QtCore.Qt.CheckState.Checked:
                    continue
                child_path = child.data(0, QtCore.Qt.ItemDataRole.UserRole)
                child_track = self._track_map.get(child_path)
                if not child_track:
                    continue
                master_track.title = master_track.title or child_track.title
                master_track.artist = master_track.artist or child_track.artist
                master_track.album = master_track.album or child_track.album
                master_track.genre = master_track.genre or child_track.genre
                master_track.bpm = master_track.bpm or child_track.bpm
                master_track.key = master_track.key or child_track.key
                changed = True
            if changed:
                update_track(master_track)
        if changed:
            self.accept()


def _safe_size(path: str) -> int | None:
    try:
        return Path(path).stat().st_size
    except Exception:
        return None


class DuplicateScanSignals(QtCore.QObject):
    progress = QtCore.pyqtSignal(int, int)
    finished = QtCore.pyqtSignal(object)


class DuplicateScanWorker(QtCore.QRunnable):
    def __init__(self, tracks: list[Track], method: str):
        super().__init__()
        self.tracks = tracks
        self.method = method
        self.signals = DuplicateScanSignals()
        self._stop = False

    def stop(self):
        self._stop = True

    def run(self):
        result = self._scan()
        self.signals.finished.emit(result)

    def _scan(self):
        if self.method == "Tagi":
            return find_duplicates_by_tags(self.tracks)

        paths = [Path(t.path) for t in self.tracks]
        updates: list[Track] = []
        stat_map: dict[str, tuple[int | None, float | None]] = {}
        for idx, track in enumerate(self.tracks, 1):
            if self._stop:
                break
            size, mtime = _stat_track(track.path)
            stat_map[track.path] = (size, mtime)
            if track.file_size != size or track.file_mtime != mtime:
                track.file_size = size
                track.file_mtime = mtime
                updates.append(track)
            self.signals.progress.emit(idx, len(self.tracks))
        if updates:
            update_tracks_file_meta(updates)

        if self.method == "Hash":
            self._ensure_hashes(stat_map)
            return self._groups_from_hash()
        if self.method == "Fingerprint":
            self._ensure_fingerprints(stat_map)
            return self._groups_from_fingerprint()
        return self._scan_staged(paths, stat_map)

    def _ensure_hashes(self, stat_map: dict[str, tuple[int | None, float | None]], subset: list[Track] | None = None):
        targets = subset or self.tracks
        updates: list[Track] = []
        for idx, track in enumerate(targets, 1):
            if self._stop:
                break
            size, mtime = stat_map.get(track.path, (track.file_size, track.file_mtime))
            if track.file_hash and track.file_mtime == mtime:
                continue
            try:
                track.file_hash = file_hash(Path(track.path))
                track.file_mtime = mtime
                track.file_size = size
                updates.append(track)
            except Exception:
                continue
            self.signals.progress.emit(idx, len(targets))
        if updates:
            update_tracks_file_meta(updates)

    def _ensure_fingerprints(
        self, stat_map: dict[str, tuple[int | None, float | None]], subset: list[Track] | None = None
    ):
        recognizer = AcoustIdRecognizer(api_key=None)
        targets = subset or self.tracks
        updates: list[Track] = []
        for idx, track in enumerate(targets, 1):
            if self._stop:
                break
            size, mtime = stat_map.get(track.path, (track.file_size, track.file_mtime))
            if track.fingerprint and track.file_mtime == mtime:
                continue
            try:
                fp = recognizer.fingerprint(Path(track.path))
            except Exception:
                fp = None
            if fp:
                _, fingerprint = fp
                track.fingerprint = fingerprint
                track.file_mtime = mtime
                track.file_size = size
                updates.append(track)
            self.signals.progress.emit(idx, len(targets))
        if updates:
            update_tracks_file_meta(updates)

    def _scan_staged(self, paths: list[Path], stat_map: dict[str, tuple[int | None, float | None]]):
        size_groups: dict[tuple[int | None, float | None], list[Track]] = {}
        for track in self.tracks:
            size, mtime = stat_map.get(track.path, (track.file_size, track.file_mtime))
            size_groups.setdefault((size, mtime), []).append(track)
        candidate_tracks = [t for group in size_groups.values() if len(group) > 1 for t in group]
        if not candidate_tracks:
            return find_duplicates_by_hash([])
        self._ensure_hashes(stat_map, subset=candidate_tracks)

        hash_groups: dict[str, list[Track]] = {}
        for track in candidate_tracks:
            if not track.file_hash:
                continue
            hash_groups.setdefault(track.file_hash, []).append(track)
        hash_candidates = [t for group in hash_groups.values() if len(group) > 1 for t in group]
        if not hash_candidates:
            return find_duplicates_by_hash([])

        self._ensure_fingerprints(stat_map, subset=hash_candidates)
        fingerprint_groups: dict[str, list[int]] = {}
        for idx, track in enumerate(self.tracks, 1):
            if track in hash_candidates and track.fingerprint:
                fingerprint_groups.setdefault(track.fingerprint, []).append(idx)
        groups = [
            DuplicateGroup(track_ids=ids, similarity=0.97)
            for ids in fingerprint_groups.values()
            if len(ids) > 1
        ]
        return DuplicateResult(groups=groups)

    def _groups_from_hash(self) -> DuplicateResult:
        hash_groups: dict[str, list[int]] = {}
        for idx, track in enumerate(self.tracks, 1):
            if not track.file_hash:
                continue
            hash_groups.setdefault(track.file_hash, []).append(idx)
        groups = [
            DuplicateGroup(track_ids=ids, similarity=1.0)
            for ids in hash_groups.values()
            if len(ids) > 1
        ]
        return DuplicateResult(groups=groups)

    def _groups_from_fingerprint(self) -> DuplicateResult:
        fp_groups: dict[str, list[int]] = {}
        for idx, track in enumerate(self.tracks, 1):
            if not track.fingerprint:
                continue
            fp_groups.setdefault(track.fingerprint, []).append(idx)
        groups = [
            DuplicateGroup(track_ids=ids, similarity=0.95)
            for ids in fp_groups.values()
            if len(ids) > 1
        ]
        return DuplicateResult(groups=groups)


def _stat_track(path: str) -> tuple[int | None, float | None]:
    try:
        stat = Path(path).stat()
        return stat.st_size, stat.st_mtime
    except Exception:
        return None, None




