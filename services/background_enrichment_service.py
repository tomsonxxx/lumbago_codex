from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from copy import deepcopy
from typing import Callable, Optional

from PyQt6 import QtCore

from core.models import BACKGROUND_AUTOTAG_FIELDS, AnalysisJob
from core.process_log_pl import format_queue_status, format_source_label, track_filename
from data import repository
from services.metadata_writeback import PendingTrackWrite, apply_track_writes

JOB_TIMEOUT_SECONDS = 90
MAX_CONCURRENT_JOBS = 1


class _BackgroundEnrichmentSignals(QtCore.QObject):
    job_finished = QtCore.pyqtSignal(int, str, str)  # job_id, status, error_msg


class BackgroundEnrichmentJobRunnable(QtCore.QRunnable):
    def __init__(
        self,
        job: AnalysisJob,
        settings,
        signals: _BackgroundEnrichmentSignals,
        *,
        timeout_seconds: int = JOB_TIMEOUT_SECONDS,
    ):
        super().__init__()
        self.job = job
        self.settings = settings
        self.signals = signals
        self.timeout_seconds = timeout_seconds
        self.setAutoDelete(True)

    def run(self) -> None:
        job_id = self.job.job_id
        try:
            execute_background_enrichment_job(self.job, self.settings, self.timeout_seconds)
            self.signals.job_finished.emit(job_id, "completed", "")
        except Exception as exc:
            repository.update_analysis_job_status(job_id, "failed", str(exc))
            self.signals.job_finished.emit(job_id, "failed", str(exc))


def execute_background_enrichment_job(
    job: AnalysisJob,
    settings,
    timeout_seconds: int = JOB_TIMEOUT_SECONDS,
) -> None:
    """Wykonuje pojedyncze zadanie uzupełniania (poza wątkiem GUI)."""
    from services.autotag_rewrite import UnifiedAutoTagger

    track = repository.get_track_by_id(job.track_id)
    if not track:
        repository.update_analysis_job_status(job.job_id, "failed", "Utwór nie istnieje w bazie")
        return

    already_filled = {
        field for field in BACKGROUND_AUTOTAG_FIELDS if getattr(track, field, None)
    }
    if len(already_filled) == len(BACKGROUND_AUTOTAG_FIELDS):
        repository.update_analysis_job_status(job.job_id, "completed")
        return

    autotagger = UnifiedAutoTagger(settings)

    def _enrich() -> tuple[object, dict]:
        result = autotagger.enrich_missing_background_fields(
            deepcopy(track),
            already_filled_fields=already_filled,
        )
        changes = autotagger.apply_background_fields(
            track,
            result,
            already_filled_fields=already_filled,
        )
        return result, changes

    with ThreadPoolExecutor(max_workers=1, thread_name_prefix="bg-enrich") as pool:
        future = pool.submit(_enrich)
        try:
            result, changes = future.result(timeout=timeout_seconds)
        except FuturesTimeoutError as exc:
            raise TimeoutError(
                f"Przekroczono limit czasu ({timeout_seconds} s) dla utworu #{job.track_id}"
            ) from exc

    source_count = len(
        [
            c
            for c in getattr(result, "candidates", []) or []
            if getattr(c, "error", None) is None and getattr(c, "score", 0) > 0
        ]
    )

    if changes:
        fields_to_write = {field: str(value) for field, value in changes.items()}
        old_values = {field: None for field in changes}
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
            raise RuntimeError(
                f"Nie udało się zapisać tagów w pliku "
                f"({len(writeback.file_write_errors)} błędów) — {track_filename(track.path)}"
            )
    elif source_count:
        _safe_process_log(
            f"[bg-service] Brak nowych pól do uzupełnienia "
            f"(sprawdzono {source_count} źródeł) — {track_filename(track.path)}"
        )

    repository.update_analysis_job_status(job.job_id, "completed")


def _safe_process_log(message: str) -> None:
    try:
        from ui.main_window import _process_log

        _process_log(message)
    except Exception:
        print(message)


class BackgroundEnrichmentService(QtCore.QObject):
    """
    Kolejka AnalysisJob dla uzupełniania tagów w tle.
    Przetwarzanie odbywa się poza wątkiem GUI (QThreadPool).
    """

    def __init__(self, settings, main_window_ref=None):
        super().__init__()
        self.settings = settings
        self.main_window_ref = main_window_ref
        self._processor_timer: Optional[QtCore.QTimer] = None
        self._signals = _BackgroundEnrichmentSignals()
        self._signals.job_finished.connect(self._on_job_finished)
        self._thread_pool = QtCore.QThreadPool.globalInstance()
        self._jobs_in_flight = 0
        self._log_fn: Callable[[str], None] = self._log

    def enqueue_background_enrichment(
        self,
        track_ids: list[int],
        priority: int = 5,
        source: str = "manual",
    ) -> list[int]:
        created_job_ids = []

        for track_id in track_ids:
            try:
                if repository.has_active_analysis_job(track_id, "background_enrichment"):
                    continue
                job = repository.create_analysis_job(
                    track_id=track_id,
                    job_type="background_enrichment",
                    priority=priority,
                )
                created_job_ids.append(job.job_id)
            except Exception as e:
                self._log(f"[bg-service] Nie udało się utworzyć zadania dla utworu #{track_id}: {e}")

        count = len(created_job_ids)
        source_label = format_source_label(source)
        if count:
            self._log(
                f"[bg-service] Dodano {count} zadań do kolejki "
                f"({source_label})"
            )
            self._dispatch_jobs()
        else:
            self._log(
                f"[bg-service] Nie dodano nowych zadań "
                f"(próbowano: {len(track_ids)}, {source_label}) — "
                "utwory już są w kolejce lub brak ID w bazie"
            )
        return created_job_ids

    def start_processor(self, interval_ms: int = 8000) -> None:
        reset = repository.reset_running_analysis_jobs_on_startup()
        if reset:
            self._log(
                f"[bg-service] Po restarcie przywrócono {reset} zawieszonych zadań do kolejki"
            )

        if self._processor_timer:
            return

        self._processor_timer = QtCore.QTimer(self)
        self._processor_timer.timeout.connect(self._on_processor_tick)
        self._processor_timer.start(interval_ms)
        self._log("[bg-service] Uruchomiono procesor zadań (działa w tle, bez blokowania okna)")
        self._dispatch_jobs()

    def stop_processor(self) -> None:
        if self._processor_timer:
            self._processor_timer.stop()
            self._processor_timer = None

    def _on_processor_tick(self) -> None:
        try:
            self._dispatch_jobs()
        except Exception as e:
            self._log(f"[bg-service] Błąd harmonogramu zadań: {e}")

    def _dispatch_jobs(self) -> None:
        if self._jobs_in_flight >= MAX_CONCURRENT_JOBS:
            return

        slots = MAX_CONCURRENT_JOBS - self._jobs_in_flight
        pending_jobs = repository.get_pending_analysis_jobs(limit=slots)
        if not pending_jobs:
            return

        for job in pending_jobs:
            if not repository.update_analysis_job_status(job.job_id, "running"):
                continue
            self._jobs_in_flight += 1
            runnable = BackgroundEnrichmentJobRunnable(job, self.settings, self._signals)
            self._thread_pool.start(runnable)

    def _on_job_finished(self, job_id: int, status: str, error_msg: str) -> None:
        self._jobs_in_flight = max(0, self._jobs_in_flight - 1)
        pending = repository.count_analysis_jobs_by_status("pending")
        running = repository.count_analysis_jobs_by_status("running")
        queue = format_queue_status(pending, running)

        if status == "completed":
            self._log(f"[bg-service] Zadanie #{job_id} ukończone ({queue})")
        else:
            self._log(f"[bg-service] Zadanie #{job_id} nie powiodło się: {error_msg} ({queue})")

        if pending > 0 and self._jobs_in_flight < MAX_CONCURRENT_JOBS:
            QtCore.QTimer.singleShot(250, self._dispatch_jobs)

    def reset_stale_running_jobs(self) -> None:
        reset = repository.reset_running_analysis_jobs_on_startup()
        if reset:
            self._log(f"[bg-service] Zresetowano {reset} zawieszonych zadań")

    def _log(self, message: str) -> None:
        _safe_process_log(message)