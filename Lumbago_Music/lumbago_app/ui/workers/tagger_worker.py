"""Lumbago Music AI — Worker AI taggera (QThread)."""

import logging
from PyQt6.QtCore import QThread, pyqtSignal

logger = logging.getLogger(__name__)


class TaggerWorker(QThread):
    """Worker QThread do tagowania AI w tle."""

    progress = pyqtSignal(int, int, str)
    finished = pyqtSignal(int, int)
    error = pyqtSignal(str)

    def __init__(self, track_ids: list[int]) -> None:
        super().__init__()
        self._track_ids = track_ids

    def run(self) -> None:
        try:
            from lumbago_app.services.ai.tagger_service import TaggerService
            service = TaggerService()
            results = service.tag_tracks(
                self._track_ids,
                progress_callback=lambda c, t, title: self.progress.emit(c, t, title),
            )
            success = sum(1 for v in results.values() if v)
            self.finished.emit(success, len(results) - success)
        except Exception as exc:
            self.error.emit(str(exc))
