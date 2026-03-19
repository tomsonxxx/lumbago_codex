"""Lumbago Music AI — Worker wykrywania duplikatów (QThread)."""

import logging
from PyQt6.QtCore import QThread, pyqtSignal

logger = logging.getLogger(__name__)


class DuplicateWorker(QThread):
    """Worker QThread do skanowania duplikatów w tle."""

    progress = pyqtSignal(str)
    finished = pyqtSignal(list)   # lista DuplicateGroup
    error = pyqtSignal(str)

    def run(self) -> None:
        raise NotImplementedError(
            "DuplicateWorker.run() — do implementacji w FAZIE 2."
        )
