"""Lumbago Music AI — Worker importu (QThread)."""

import logging
from pathlib import Path
from typing import Optional
from PyQt6.QtCore import QThread, pyqtSignal

logger = logging.getLogger(__name__)


class ImportWorker(QThread):
    """Worker QThread do importu w tle."""

    progress = pyqtSignal(int, int, str)    # current, total, filename
    finished = pyqtSignal(int, int, int)    # added, skipped, failed
    error = pyqtSignal(str)

    def __init__(
        self,
        directory: Optional[Path] = None,
        files: Optional[list[Path]] = None,
        recursive: bool = True,
    ) -> None:
        super().__init__()
        self._directory = directory
        self._files = files
        self._recursive = recursive

    def run(self) -> None:
        try:
            from lumbago_app.services.import_service import ImportService
            service = ImportService()
            cb = lambda c, t, f: self.progress.emit(c, t, f)

            if self._directory:
                r = service.import_directory(self._directory, self._recursive, cb)
            elif self._files:
                r = service.import_files(self._files, cb)
            else:
                self.error.emit("Brak źródła importu")
                return

            self.finished.emit(r.added, r.skipped, r.failed)
        except Exception as exc:
            self.error.emit(str(exc))
