"""Lumbago Music AI — Worker fingerprintingu (QThread)."""

import logging
from PyQt6.QtCore import QThread, pyqtSignal

logger = logging.getLogger(__name__)


class FingerprintWorker(QThread):
    """Worker QThread do generowania fingerprintów w tle."""

    progress = pyqtSignal(int, int, str)
    finished = pyqtSignal(int, int)
    error = pyqtSignal(str)

    def __init__(self, track_ids: list[int]) -> None:
        super().__init__()
        self._track_ids = track_ids

    def run(self) -> None:
        raise NotImplementedError(
            "FingerprintWorker.run() — do implementacji w FAZIE 2."
        )
