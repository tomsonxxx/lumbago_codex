"""Lumbago Music AI — Worker analizy audio (QThread)."""

import logging
from PyQt6.QtCore import QThread, pyqtSignal

logger = logging.getLogger(__name__)


class AnalysisWorker(QThread):
    """Worker QThread do analizy audio w tle."""

    progress = pyqtSignal(int, int, str)
    finished = pyqtSignal(int, int)    # success, failed
    error = pyqtSignal(str)

    def __init__(self, track_ids: list[int]) -> None:
        super().__init__()
        self._track_ids = track_ids

    def run(self) -> None:
        """
        Analizuje BPM, tonację i LUFS dla podanych ID.
        Do pełnej implementacji w FAZIE 2.
        """
        raise NotImplementedError(
            "AnalysisWorker.run() — do implementacji w FAZIE 2.\n"
            "Plan: dla każdego track_id wywołaj AudioAnalyzer.analyze()\n"
            "i LUFSService.measure(), zapisz wyniki do bazy."
        )
