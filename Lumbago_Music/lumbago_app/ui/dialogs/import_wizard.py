"""
Lumbago Music AI — Wizard importu
===================================
Dialog prowadzący przez import katalogu/plików.
"""

import logging
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QProgressBar, QTextEdit, QCheckBox,
)

logger = logging.getLogger(__name__)


class _ImportWorker(QThread):
    """Worker thread dla importu."""
    progress = pyqtSignal(int, int, str)
    finished = pyqtSignal(int, int, int)  # (added, skipped, failed)
    error = pyqtSignal(str)

    def __init__(
        self,
        directory: Optional[str] = None,
        file_paths: Optional[list[str]] = None,
        recursive: bool = True,
    ) -> None:
        super().__init__()
        self._directory = directory
        self._file_paths = file_paths
        self._recursive = recursive

    def run(self) -> None:
        try:
            from lumbago_app.services.import_service import ImportService
            service = ImportService()

            if self._directory:
                result = service.import_directory(
                    Path(self._directory),
                    recursive=self._recursive,
                    progress_callback=lambda c, t, f: self.progress.emit(c, t, f),
                )
            elif self._file_paths:
                result = service.import_files(
                    [Path(p) for p in self._file_paths],
                    progress_callback=lambda c, t, f: self.progress.emit(c, t, f),
                )
            else:
                self.error.emit("Brak źródła importu")
                return

            self.finished.emit(result.added, result.skipped, result.failed)
        except Exception as exc:
            self.error.emit(str(exc))


class ImportWizard(QDialog):
    """Wizard importu plików audio."""

    def __init__(
        self,
        directory: Optional[str] = None,
        file_paths: Optional[list[str]] = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._directory = directory
        self._file_paths = file_paths
        self._worker: Optional[_ImportWorker] = None
        self.setWindowTitle("Importuj bibliotekę muzyczną")
        self.setMinimumWidth(480)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Informacja o źródle
        if self._directory:
            source_text = f"Katalog: {self._directory}"
        elif self._file_paths:
            source_text = f"Pliki: {len(self._file_paths)} szt."
        else:
            source_text = "Brak źródła"

        self._source_label = QLabel(source_text)
        self._source_label.setStyleSheet("color: #00f5ff;")
        layout.addWidget(self._source_label)

        # Opcje
        self._recursive_cb = QCheckBox("Skanuj podkatalogi rekurencyjnie")
        self._recursive_cb.setChecked(True)
        if self._file_paths:
            self._recursive_cb.setEnabled(False)
        layout.addWidget(self._recursive_cb)

        # Postęp
        self._progress = QProgressBar()
        self._progress.setRange(0, 0)  # indeterminate
        layout.addWidget(self._progress)

        self._log = QTextEdit()
        self._log.setReadOnly(True)
        self._log.setMaximumHeight(150)
        layout.addWidget(self._log)

        # Przyciski
        btn_layout = QHBoxLayout()
        self._btn_cancel = QPushButton("Anuluj")
        self._btn_cancel.clicked.connect(self._on_cancel)
        self._btn_start = QPushButton("▶  Importuj")
        self._btn_start.setProperty("accent", True)
        self._btn_start.clicked.connect(self._on_start)
        btn_layout.addWidget(self._btn_cancel)
        btn_layout.addWidget(self._btn_start)
        layout.addLayout(btn_layout)

    def _on_start(self) -> None:
        self._btn_start.setEnabled(False)
        self._log.append("Rozpoczynam import...")
        self._progress.setRange(0, 0)

        self._worker = _ImportWorker(
            directory=self._directory,
            file_paths=self._file_paths,
            recursive=self._recursive_cb.isChecked(),
        )
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_finished)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_progress(self, current: int, total: int, filename: str) -> None:
        if total > 0:
            self._progress.setRange(0, total)
            self._progress.setValue(current)
        self._log.append(f"[{current}/{total}] {filename}")

    def _on_finished(self, added: int, skipped: int, failed: int) -> None:
        self._progress.setRange(0, 100)
        self._progress.setValue(100)
        self._log.append(
            f"\nImport zakończony:\n"
            f"  Dodano: {added}\n"
            f"  Pominięto: {skipped}\n"
            f"  Błędów: {failed}"
        )
        self._btn_cancel.setText("Zamknij")
        self._btn_cancel.clicked.disconnect()
        self._btn_cancel.clicked.connect(self.accept)

    def _on_error(self, msg: str) -> None:
        self._log.append(f"\nBŁĄD: {msg}")
        self._btn_start.setEnabled(True)

    def _on_cancel(self) -> None:
        if self._worker and self._worker.isRunning():
            self._worker.terminate()
        self.reject()
