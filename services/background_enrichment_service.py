from __future__ import annotations

from typing import Optional
from datetime import datetime

from core.models import AnalysisJob
from data import repository
from services.metadata_writeback import PendingTrackWrite, apply_track_writes
from PyQt6 import QtCore


class BackgroundEnrichmentService:
    """
    Serwis zarządzający kolejką zadań AnalysisJob dla uzupełniania tagów w tle.
    """

    def __init__(self, settings, main_window_ref=None):
        self.settings = settings
        self.main_window_ref = main_window_ref  # do logowania i UI
        self._processor_timer: Optional[QtCore.QTimer] = None
        self._is_processing = False

    def enqueue_background_enrichment(
        self,
        track_ids: list[int],
        priority: int = 5,
        source: str = "manual"
    ) -> list[int]:
        """
        Tworzy zadania AnalysisJob dla podanych tracków.
        Zwraca listę utworzonych job_id.
        """
        created_job_ids = []

        for track_id in track_ids:
            try:
                job = repository.create_analysis_job(
                    track_id=track_id,
                    job_type="background_enrichment",
                    priority=priority,
                )
                created_job_ids.append(job.job_id)
            except Exception as e:
                self._log(f"[bg-service] Błąd tworzenia zadania dla track_id={track_id}: {e}")

        self._log(f"[bg-service] Utworzono {len(created_job_ids)} zadań background_enrichment (źródło: {source})")
        return created_job_ids

    def process_pending_jobs(self, max_jobs: int = 5) -> int:
        """
        Przetwarza do max_jobs oczekujących zadań.
        Zwraca liczbę przetworzonych zadań.
        """
        if self._is_processing:
            return 0

        self._is_processing = True
        processed = 0

        try:
            pending_jobs = repository.get_pending_analysis_jobs(limit=max_jobs)

            for job in pending_jobs:
                if not self._process_single_job(job):
                    break  # przerwij jeśli coś poszło nie tak (np. worker już działa)
                processed += 1

        finally:
            self._is_processing = False

        return processed

    def _process_single_job(self, job: AnalysisJob) -> bool:
        """Przetwarza pojedyncze zadanie. Zwraca True jeśli zadanie zostało podjęte."""
        # Oznacz jako running
        success = repository.update_analysis_job_status(job.job_id, "running")
        if not success:
            return False

        try:
            # Pobierz track
            track = repository.get_track_by_id(job.track_id)
            if not track:
                repository.update_analysis_job_status(job.job_id, "failed", "Track nie istnieje")
                return True

            # Uruchom właściwe uzupełnianie (używamy istniejącego workera)
            # Na razie robimy to synchronicznie w ramach procesora (proste rozwiązanie na start)
            # W przyszłości można to przenieść do osobnego wątku.

            from copy import deepcopy
            from services.autotag_rewrite import UnifiedAutoTagger

            autotagger = UnifiedAutoTagger(self.settings)

            result = autotagger.enrich_missing_background_fields(
                deepcopy(track)
            )

            if result.best_match:
                # Jedna ścieżka writebacku dla background enrichment:
                # DB + changelog + plik tagów przechodzą przez wspólny helper.
                background_fields = ["originalartist", "rating", "comment", "lyrics", "remixer"]
                fields_to_write: dict[str, str] = {}
                old_values: dict[str, str | None] = {}
                for field in background_fields:
                    value = getattr(result.best_match, field, None)
                    current = getattr(track, field, None)
                    if value and not current:
                        setattr(track, field, value)
                        fields_to_write[field] = str(value)
                        old_values[field] = None if current is None else str(current)

                if fields_to_write:
                    writeback = apply_track_writes(
                        [
                            PendingTrackWrite(
                                track=track,
                                fields=fields_to_write,
                                source="background_enrichment",
                                confidence=None,
                                change_log_source="background_enrichment",
                                old_values=old_values,
                            )
                        ],
                        max_workers=1,
                        update_mode="single",
                    )
                    if writeback.file_write_errors:
                        self._log(
                            f"[bg-service] writeback errors for track_id={job.track_id}: "
                            f"{len(writeback.file_write_errors)}"
                        )

            repository.update_analysis_job_status(job.job_id, "completed")
            self._log(f"[bg-service] Zakończono zadanie #{job.job_id} dla track_id={job.track_id}")

        except Exception as e:
            repository.update_analysis_job_status(job.job_id, "failed", str(e))
            self._log(f"[bg-service] Błąd przetwarzania zadania #{job.job_id}: {e}")

        return True

    def start_processor(self, interval_ms: int = 8000):
        """Uruchamia timer, który co pewien czas sprawdza oczekujące zadania."""
        if self._processor_timer:
            return

        self._processor_timer = QtCore.QTimer()
        self._processor_timer.timeout.connect(self._on_processor_tick)
        self._processor_timer.start(interval_ms)
        self._log("[bg-service] Procesor zadań w tle uruchomiony")

    def _on_processor_tick(self):
        try:
            processed = self.process_pending_jobs(max_jobs=3)
            if processed > 0:
                self._log(f"[bg-service] Przetworzono {processed} zadań w tle")
        except Exception as e:
            self._log(f"[bg-service] Błąd w procesorze: {e}")

    def stop_processor(self):
        if self._processor_timer:
            self._processor_timer.stop()
            self._processor_timer = None

    def _log(self, message: str):
        try:
            from ui.main_window import _process_log
            _process_log(message)
        except Exception:
            print(message)

    def reset_stale_running_jobs(self):
        """Przy starcie aplikacji resetuje zadania, które zostały w stanie 'running'."""
        # Na razie prosty mechanizm – w pełnej wersji można by to zrobić w repo
        pass
