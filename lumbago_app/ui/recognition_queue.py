from __future__ import annotations

from PyQt6 import QtCore

from lumbago_app.core.models import Track
from lumbago_app.services.metadata_enricher import MetadataEnricher
from lumbago_app.ui.recognition_results_dialog import RecognitionResult


class RecognitionSignals(QtCore.QObject):
    progress = QtCore.pyqtSignal(int, int)
    finished = QtCore.pyqtSignal(list)


class RecognitionBatchWorker(QtCore.QRunnable):
    def __init__(
        self,
        tracks: list[Track],
        acoustid_key: str | None,
        musicbrainz_app: str | None,
        validation_policy: str | None = None,
        cache_ttl_days: int = 30,
    ):
        super().__init__()
        self.tracks = tracks
        self.acoustid_key = acoustid_key
        self.musicbrainz_app = musicbrainz_app
        self.validation_policy = validation_policy
        self.cache_ttl_days = cache_ttl_days
        self.signals = RecognitionSignals()
        self._stop_requested = False

    def stop(self) -> None:
        self._stop_requested = True

    def run(self) -> None:
        enricher = MetadataEnricher(
            self.acoustid_key,
            self.musicbrainz_app,
            validation_policy=self.validation_policy,
            cache_ttl_days=self.cache_ttl_days,
        )
        results: list[RecognitionResult] = []
        total = len(self.tracks)
        for idx, track in enumerate(self.tracks, 1):
            if self._stop_requested:
                break
            orig_title = track.title
            orig_artist = track.artist
            orig_album = track.album
            orig_year = track.year
            orig_genre = track.genre
            orig_artwork = track.artwork_path
            updated = None
            try:
                updated = enricher.enrich_track(track)
            except Exception:
                updated = None
            results.append(
                RecognitionResult(
                    track=track,
                    original_title=orig_title,
                    original_artist=orig_artist,
                    original_album=orig_album,
                    original_year=orig_year,
                    original_genre=orig_genre,
                    original_artwork=orig_artwork,
                    success=updated is not None,
                )
            )
            self.signals.progress.emit(idx, total)
        self.signals.finished.emit(results)
