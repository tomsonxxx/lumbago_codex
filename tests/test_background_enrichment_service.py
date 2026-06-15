from __future__ import annotations

import tempfile
from unittest.mock import MagicMock, patch

import pytest
from PyQt6 import QtCore

from core.models import AnalysisJob, Track
from data.db import reset_engine
from data.repository import (
    count_analysis_jobs_by_status,
    create_analysis_job,
    get_pending_analysis_jobs,
    init_db,
    reset_running_analysis_jobs_on_startup,
    update_analysis_job_status,
    upsert_tracks,
)
from services.background_enrichment_service import (
    BackgroundEnrichmentService,
    execute_background_enrichment_job,
)


@pytest.fixture
def temp_db(monkeypatch):
    with tempfile.TemporaryDirectory() as temp_dir:
        monkeypatch.setenv("APPDATA", temp_dir)
        reset_engine()
        init_db()
        yield
        reset_engine()


def test_reset_running_analysis_jobs_on_startup(temp_db):
    upsert_tracks([Track(path="a.mp3", title="A")])
    from data.repository import list_tracks

    track_id = list_tracks()[0].id
    job = create_analysis_job(track_id, "background_enrichment")
    update_analysis_job_status(job.job_id, "running")

    reset = reset_running_analysis_jobs_on_startup()
    assert reset == 1
    pending = get_pending_analysis_jobs()
    assert len(pending) == 1
    assert pending[0].status == "pending"


def test_execute_background_enrichment_job_completes_when_fields_filled(temp_db):
    upsert_tracks(
        [
            Track(
                path="a.mp3",
                title="A",
                originalartist="OA",
                rating=3,
                comment="ok",
                lyrics="x",
                remixer="DJ",
            )
        ]
    )
    from data.repository import list_tracks

    track = list_tracks()[0]
    job = create_analysis_job(track.id, "background_enrichment")
    update_analysis_job_status(job.job_id, "running")

    class S:
        provider_parallel_workers = 2

    execute_background_enrichment_job(job, S(), timeout_seconds=5)

    pending = count_analysis_jobs_by_status("pending")
    running = count_analysis_jobs_by_status("running")
    assert pending == 0
    assert running == 0


def test_background_service_dispatches_without_blocking_ui(temp_db):
    upsert_tracks([Track(path="a.mp3", title="Song", artist="Artist")])
    from data.repository import list_tracks

    track_id = list_tracks()[0].id
    create_analysis_job(track_id, "background_enrichment")

    class S:
        provider_parallel_workers = 2

    app = QtCore.QCoreApplication.instance() or QtCore.QCoreApplication([])
    service = BackgroundEnrichmentService(S())
    done = {"ok": False}

    def _fake_execute(job, settings, timeout_seconds=90):
        update_analysis_job_status(job.job_id, "completed")

    service._signals.job_finished.connect(lambda *_: done.update(ok=True))

    with patch(
        "services.background_enrichment_service.execute_background_enrichment_job",
        side_effect=_fake_execute,
    ):
        service._dispatch_jobs()
        service._thread_pool.waitForDone(5000)
        for _ in range(20):
            app.processEvents()
            if done["ok"]:
                break

    assert done["ok"]
    assert service._jobs_in_flight == 0
    assert count_analysis_jobs_by_status("pending") == 0