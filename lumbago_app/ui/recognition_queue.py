from __future__ import annotations

import logging

from PyQt6 import QtCore

from lumbago_app.core.models import Track
from lumbago_app.data.repository import update_track
from lumbago_app.services.metadata_enricher import MetadataEnricher

log = logging.getLogger(__name__)


class RecognitionSignals(QtCore.QObject):
    progress = QtCore.pyqtSignal(int, int)
    finished = QtCore.pyqtSignal(int, int)


class RecognitionBatchWorker(QtCore.QRunnable):
    def __init__(
        self,
        tracks: list[Track],
        musicbrainz_app: str | None,
        validation_policy: str | None = None,
        cache_ttl_days: int = 30,
        acoustid_api_key: str | None = None,
    ):
        super().__init__()
        self.tracks = tracks
        self.musicbrainz_app = musicbrainz_app
        self.validation_policy = validation_policy
        self.cache_ttl_days = cache_ttl_days
        self.acoustid_api_key = acoustid_api_key
        self.signals = RecognitionSignals()
        self._stop_requested = False

    def stop(self) -> None:
        self._stop_requested = True

    def run(self) -> None:
        enricher = MetadataEnricher(
            self.musicbrainz_app,
            validation_policy=self.validation_policy,
            cache_ttl_days=self.cache_ttl_days,
            acoustid_api_key=self.acoustid_api_key,
        )
        processed = 0
        errors = 0
        total = len(self.tracks)
        for track in self.tracks:
            if self._stop_requested:
                break
            updated = None
            try:
                updated = enricher.enrich_track(track)
            except Exception as exc:
                log.warning("Recognition failed for %s: %s", track.path, exc)
                updated = None
            if updated:
                update_track(updated)
            else:
                errors += 1
                log.debug("No match found for %s", track.path)
            processed += 1
            self.signals.progress.emit(processed, total)
        self.signals.finished.emit(processed, errors)
