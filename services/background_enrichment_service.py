from __future__ import annotations

from typing import Optional
from datetime import datetime

from core.models import BACKGROUND_AUTOTAG_FIELDS, AnalysisJob
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

        count = len(created_job_ids)
        if count:
            self._log(
                f"[bg-service] Utworzono {count} nowych zadań uzupełniania w tle "
                f"(źródło: {source})"
            )
        else:
            self._log(
                f"[bg-service] 0 nowych zadań — brak poprawnych ID utworów "
                f"(próbowano: {len(track_ids)}, źródło: {source})"
            )
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

            already_filled = {
                field
                for field in BACKGROUND_AUTOTAG_FIELDS
                if getattr(track, field, None)
            }
            if len(already_filled) == len(BACKGROUND_AUTOTAG_FIELDS):
                repository.update_analysis_job_status(job.job_id, "completed")
                return True

            result = autotagger.enrich_missing_background_fields(
                deepcopy(track),
                already_filled_fields=already_filled,
            )
            source_count = len(
                [
                    c
                    for c in getattr(result, "candidates", []) or []
                    if getattr(c, "error", None) is None and getattr(c, "score", 0) > 0
                ]
            )
            changes = autotagger.apply_background_fields(
                track,
                result,
                already_filled_fields=already_filled,
            )
            if not changes:
                if source_count:
                    self._log(
                        f"[bg-service] Brak pól tła po {source_count} źródłach "
                        f"dla track_id={job.track_id}"
                    )
            else:
                fields_to_write: dict[str, str] = {field: str(value) for field, value in changes.items()}
                old_values: dict[str, str | None] = {field: None for field in changes}

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
