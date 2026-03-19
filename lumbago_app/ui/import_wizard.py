from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PyQt6 import QtCore, QtWidgets
from lumbago_app.ui.widgets import apply_dialog_fade, dialog_icon_pixmap

from lumbago_app.core.config import cache_dir
from lumbago_app.core.audio import extract_metadata, iter_audio_files
from lumbago_app.core.models import Track
from lumbago_app.data.repository import upsert_tracks


@dataclass
class ImportOptions:
    folder: Path
    recursive: bool
    extensions: set[str]


class ScanWizardSignals(QtCore.QObject):
    progress = QtCore.pyqtSignal(int, int)
    finished = QtCore.pyqtSignal(list, list, bool)


class ImportWizardSignals(QtCore.QObject):
    progress = QtCore.pyqtSignal(int, int)
    finished = QtCore.pyqtSignal(list, bool)


class ScanWizardWorker(QtCore.QRunnable):
    def __init__(self, options: ImportOptions):
        super().__init__()
        self.options = options
        self.signals = ScanWizardSignals()
        self._stop = False

    def stop(self):
        self._stop = True

    def run(self):
        files = list(
            iter_audio_files(
                self.options.folder,
                recursive=self.options.recursive,
                extensions=self.options.extensions,
            )
        )
        total = len(files)
        tracks: list[Track] = []
        errors: list[dict[str, Any]] = []
        canceled = False
        for idx, path in enumerate(files, 1):
            if self._stop:
                canceled = True
                break
            try:
                track = extract_metadata(path)
                tracks.append(track)
            except Exception as exc:
                errors.append({"path": str(path), "stage": "scan", "error": str(exc)})
            self.signals.progress.emit(idx, total)
        self.signals.finished.emit(tracks, errors, canceled)


class ImportWizardWorker(QtCore.QRunnable):
    def __init__(self, tracks: list[Track], batch_size: int):
        super().__init__()
        self.tracks = tracks
        self.batch_size = max(1, batch_size)
        self.signals = ImportWizardSignals()
        self._stop = False

    def stop(self):
        self._stop = True

    def run(self):
        errors: list[dict[str, Any]] = []
        canceled = False
        total = len(self.tracks)
        processed = 0
        for start in range(0, total, self.batch_size):
            if self._stop:
                canceled = True
                break
            batch = self.tracks[start : start + self.batch_size]
            try:
                upsert_tracks(batch)
            except Exception as exc:
                for track in batch:
                    errors.append(
                        {
                            "path": track.path,
                            "stage": "import",
                            "error": str(exc),
                        }
                    )
            processed = min(total, start + len(batch))
            self.signals.progress.emit(processed, total)
        self.signals.finished.emit(errors, canceled)


class ImportWizard(QtWidgets.QDialog):
    def __init__(self, parent=None, on_complete=None):
        super().__init__(parent)
        self.setWindowTitle("Kreator importu")
        self.setMinimumSize(720, 480)
        apply_dialog_fade(self)
        self.on_complete = on_complete
        self.thread_pool = QtCore.QThreadPool.globalInstance()
        self._tracks: list[Track] = []
        self._errors: list[dict[str, Any]] = []
        self._scan_worker: ScanWizardWorker | None = None
        self._import_worker: ImportWizardWorker | None = None
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

        self.stack = QtWidgets.QStackedWidget()
        layout.addWidget(self.stack, 1)

        self.page_select = self._build_select_page()
        self.page_options = self._build_options_page()
        self.page_preview = self._build_preview_page()
        self.page_import = self._build_import_page()
        self.page_watch = self._build_watch_page()

        self.stack.addWidget(self.page_select)
        self.stack.addWidget(self.page_options)
        self.stack.addWidget(self.page_preview)
        self.stack.addWidget(self.page_import)
        self.stack.addWidget(self.page_watch)

        nav = QtWidgets.QHBoxLayout()
        nav.addStretch(1)
        self.back_btn = QtWidgets.QPushButton("Wstecz")
        self.back_btn.clicked.connect(self._back)
        self.next_btn = QtWidgets.QPushButton("Dalej")
        self.next_btn.clicked.connect(self._next)
        self.cancel_btn = QtWidgets.QPushButton("Anuluj")
        self.cancel_btn.clicked.connect(self.reject)
        nav.addWidget(self.back_btn)
        nav.addWidget(self.next_btn)
        nav.addWidget(self.cancel_btn)
        layout.addLayout(nav)

        self._update_nav()

    def _build_select_page(self) -> QtWidgets.QWidget:
        page = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(page)
        layout.addWidget(QtWidgets.QLabel("Krok 1: Wybierz folder"))
        row = QtWidgets.QHBoxLayout()
        self.folder_input = QtWidgets.QLineEdit()
        self.folder_input.setPlaceholderText("Wybierz folder z muzyką")
        browse = QtWidgets.QPushButton("Przeglądaj")
        browse.clicked.connect(self._browse_folder)
        row.addWidget(self.folder_input, 1)
        row.addWidget(browse)
        layout.addLayout(row)
        layout.addStretch(1)
        return page

    def _build_options_page(self) -> QtWidgets.QWidget:
        page = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(page)
        layout.addWidget(QtWidgets.QLabel("Krok 2: Opcje skanowania"))
        self.recursive_check = QtWidgets.QCheckBox("Skanowanie rekurencyjne")
        self.recursive_check.setChecked(True)
        layout.addWidget(self.recursive_check)

        self.ext_input = QtWidgets.QLineEdit()
        self.ext_input.setPlaceholderText(".mp3,.flac,.wav,.m4a,.ogg,.aac")
        self.ext_input.setText(".mp3,.flac,.wav,.m4a,.ogg,.aac")
        layout.addWidget(QtWidgets.QLabel("Rozszerzenia (oddzielone przecinkami)"))
        layout.addWidget(self.ext_input)

        self.batch_size = QtWidgets.QSpinBox()
        self.batch_size.setRange(10, 5000)
        self.batch_size.setValue(200)
        layout.addWidget(QtWidgets.QLabel("Batch commit (ile plików na zapis)"))
        layout.addWidget(self.batch_size)
        layout.addStretch(1)
        return page

    def _build_preview_page(self) -> QtWidgets.QWidget:
        page = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(page)
        layout.addWidget(QtWidgets.QLabel("Krok 3: Podgląd"))
        self.preview_table = QtWidgets.QTableWidget(0, 4)
        self.preview_table.setHorizontalHeaderLabels(["Title", "Artist", "Album", "Path"])
        self.preview_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.preview_table, 1)
        self.scan_progress = QtWidgets.QProgressBar()
        layout.addWidget(self.scan_progress)
        return page

    def _build_watch_page(self) -> QtWidgets.QWidget:
        page = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(page)
        layout.addWidget(QtWidgets.QLabel("Krok 5: Monitorowanie folderu"))
        self.watch_check = QtWidgets.QCheckBox("Monitoruj ten folder automatycznie")
        self.watch_check.setChecked(True)
        layout.addWidget(self.watch_check)
        self.watch_folder_label = QtWidgets.QLineEdit()
        self.watch_folder_label.setReadOnly(True)
        self.watch_folder_label.setPlaceholderText("Folder zostanie ustawiony po imporcie")
        layout.addWidget(self.watch_folder_label)
        self.watch_status = QtWidgets.QLabel("")
        layout.addWidget(self.watch_status)
        layout.addStretch(1)
        return page

    def _build_import_page(self) -> QtWidgets.QWidget:
        page = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(page)
        layout.addWidget(QtWidgets.QLabel("Krok 4: Import"))
        self.import_progress = QtWidgets.QProgressBar()
        self.import_progress.setRange(0, 100)
        layout.addWidget(self.import_progress)
        self.import_status = QtWidgets.QLabel("Gotowe do importu.")
        layout.addWidget(self.import_status)
        self.error_btn = QtWidgets.QPushButton("Zapisz raport błędów")
        self.error_btn.setEnabled(False)
        self.error_btn.clicked.connect(self._save_error_report)
        layout.addWidget(self.error_btn)
        return page

    def _browse_folder(self):
        folder = QtWidgets.QFileDialog.getExistingDirectory(self, "Wybierz folder z muzyką")
        if folder:
            self.folder_input.setText(folder)

    def _options(self) -> ImportOptions | None:
        folder = self.folder_input.text().strip()
        if not folder:
            QtWidgets.QMessageBox.warning(self, "Import", "Najpierw wybierz folder.")
            return None
        extensions = {
            e.strip().lower()
            for e in self.ext_input.text().split(",")
            if e.strip().startswith(".")
        }
        if not extensions:
            extensions = {".mp3", ".flac", ".wav", ".m4a", ".ogg", ".aac"}
        return ImportOptions(
            folder=Path(folder),
            recursive=self.recursive_check.isChecked(),
            extensions=extensions,
        )

    def _next(self):
        idx = self.stack.currentIndex()
        if idx == 0:
            if not self.folder_input.text().strip():
                QtWidgets.QMessageBox.warning(self, "Import", "Najpierw wybierz folder.")
                return
        if idx == 1:
            self._start_scan()
        if idx == 2:
            self._start_import()
        if idx == 4:
            self._finish_watch()
            return
        if idx < self.stack.count() - 1:
            self.stack.setCurrentIndex(idx + 1)
        self._update_nav()

    def _back(self):
        idx = self.stack.currentIndex()
        if idx > 0:
            self.stack.setCurrentIndex(idx - 1)
        self._update_nav()

    def _update_nav(self):
        idx = self.stack.currentIndex()
        self.back_btn.setEnabled(idx > 0)
        last_idx = self.stack.count() - 1
        if idx == last_idx:
            self.next_btn.setText("Zakończ")
            self.next_btn.setEnabled(True)
        else:
            self.next_btn.setText("Dalej")
            self.next_btn.setEnabled(True)

    def _start_scan(self):
        self.preview_table.setRowCount(0)
        self.scan_progress.setValue(0)
        self._errors = []
        options = self._options()
        if not options:
            return
        self._scan_worker = ScanWizardWorker(options)
        self._scan_worker.signals.progress.connect(self._scan_progress)
        self._scan_worker.signals.finished.connect(self._scan_finished)
        self.thread_pool.start(self._scan_worker)

    def _scan_progress(self, current: int, total: int):
        self.scan_progress.setMaximum(total or 1)
        self.scan_progress.setValue(current)

    def _scan_finished(self, tracks: list[Track], errors: list[dict[str, Any]], canceled: bool):
        self._tracks = tracks
        self._errors.extend(errors)
        for track in tracks[:500]:
            row = self.preview_table.rowCount()
            self.preview_table.insertRow(row)
            self.preview_table.setItem(row, 0, QtWidgets.QTableWidgetItem(track.title or ""))
            self.preview_table.setItem(row, 1, QtWidgets.QTableWidgetItem(track.artist or ""))
            self.preview_table.setItem(row, 2, QtWidgets.QTableWidgetItem(track.album or ""))
            self.preview_table.setItem(row, 3, QtWidgets.QTableWidgetItem(track.path))
        if canceled:
            QtWidgets.QMessageBox.information(self, "Import", "Skanowanie anulowane.")

    def _start_import(self):
        if not self._tracks:
            self.import_status.setText("Brak utworów do importu.")
            return
        self.import_progress.setRange(0, len(self._tracks))
        self.import_progress.setValue(0)
        self.import_status.setText("Import w toku...")
        self._import_worker = ImportWizardWorker(self._tracks, self.batch_size.value())
        self._import_worker.signals.progress.connect(self._import_progress)
        self._import_worker.signals.finished.connect(self._import_finished)
        self.thread_pool.start(self._import_worker)

    def _import_progress(self, current: int, total: int):
        self.import_progress.setMaximum(total or 1)
        self.import_progress.setValue(current)

    def _import_finished(self, errors: list[dict[str, Any]], canceled: bool):
        self._errors.extend(errors)
        self.error_btn.setEnabled(bool(self._errors))
        if canceled:
            self.import_status.setText("Import anulowany.")
            return
        self.import_progress.setValue(self.import_progress.maximum())
        self.import_status.setText(f"Zaimportowano {len(self._tracks)} utworów.")
        if self.on_complete:
            self.on_complete()
        self.watch_folder_label.setText(self.folder_input.text().strip())
        self.stack.setCurrentIndex(4)
        self._update_nav()

    def _finish_watch(self):
        if self.watch_check.isChecked():
            try:
                parent = self.parent()
                if parent is not None and hasattr(parent, "_watch_folder_svc"):
                    folder_text = self.folder_input.text().strip()
                    if folder_text:
                        parent._watch_folder_svc.add_folder(Path(folder_text))
                        self.watch_status.setText("Folder dodany do monitorowania.")
            except Exception as exc:
                self.watch_status.setText(f"Błąd monitorowania: {exc}")
        self.accept()

    def _save_error_report(self):
        if not self._errors:
            return
        default_path = str(cache_dir() / "import_errors.txt")
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Zapisz raport błędów",
            default_path,
            "TXT (*.txt)",
        )
        if not path:
            return
        lines = []
        for err in self._errors:
            lines.append(f"{err.get('stage','')} | {err.get('path','')} | {err.get('error','')}")
        Path(path).write_text("\n".join(lines), encoding="utf-8")

    def reject(self):
        if self._scan_worker:
            self._scan_worker.stop()
        if self._import_worker:
            self._import_worker.stop()
        super().reject()




