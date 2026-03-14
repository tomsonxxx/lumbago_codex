from __future__ import annotations

from PyQt6 import QtCore

from lumbago_app.core.models import Track
from lumbago_app.data.repository import update_track
from lumbago_app.services.metadata_enricher import MetadataEnricher


class RecognitionSignals(QtCore.QObject):
    progress = QtCore.pyqtSignal(int, int)
    finished = QtCore.pyqtSignal(int, int)


class RecognitionBatchWorker(QtCore.QRunnable):
    def __init__(self, tracks: list[Track], acoustid_key: str | None, musicbrainz_app: str | None):
        super().__init__()
        self.tracks = tracks
        self.acoustid_key = acoustid_key
        self.musicbrainz_app = musicbrainz_app
        self.signals = RecognitionSignals()
        self._stop_requested = False

    def stop(self) -> None:
        self._stop_requested = True

    def run(self) -> None:
        enricher = MetadataEnricher(self.acoustid_key, self.musicbrainz_app)
        processed = 0
        errors = 0
        total = len(self.tracks)
        for track in self.tracks:
            if self._stop_requested:
                break
            updated = None
            try:
                updated = enricher.enrich_track(track)
            except Exception:
                updated = None
            if updated:
                update_track(updated)
            else:
                errors += 1
            processed += 1
            self.signals.progress.emit(processed, total)
        self.signals.finished.emit(processed, errors)
