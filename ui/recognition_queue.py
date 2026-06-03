from __future__ import annotations

import logging

from PyQt6 import QtCore

from core.models import Track
from services.metadata_writeback import PendingTrackWrite, apply_track_writes
from services.metadata_enricher import MetadataEnricher

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
        track_fields = (
            "title",
            "artist",
            "album",
            "albumartist",
            "year",
            "genre",
            "tracknumber",
            "discnumber",
            "composer",
            "bpm",
            "key",
            "rating",
            "mood",
            "energy",
            "comment",
            "lyrics",
            "isrc",
            "publisher",
            "grouping",
            "copyright",
            "remixer",
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
                changed_fields = {
                    field: "" if getattr(updated, field, None) is None else str(getattr(updated, field, None))
                    for field in track_fields
                    if getattr(track, field, None) != getattr(updated, field, None)
                }
                if changed_fields:
                    old_values = {
                        field: None if getattr(track, field, None) is None else str(getattr(track, field, None))
                        for field in changed_fields
                    }
                    try:
                        apply_track_writes(
                            [
                                PendingTrackWrite(
                                    track=updated,
                                    fields=changed_fields,
                                    source="recognition_batch",
                                    confidence=None,
                                    change_log_source="recognition_batch",
                                    old_values=old_values,
                                )
                            ],
                            max_workers=1,
                            update_mode="single",
                        )
                    except Exception as exc:
                        log.warning("Recognition writeback failed for %s: %s", track.path, exc)
                        errors += 1
                        processed += 1
                        self.signals.progress.emit(processed, total)
                        continue
            else:
                errors += 1
                log.debug("No match found for %s", track.path)
            processed += 1
            self.signals.progress.emit(processed, total)
        self.signals.finished.emit(processed, errors)
