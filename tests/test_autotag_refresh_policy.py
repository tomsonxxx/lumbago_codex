from __future__ import annotations

from copy import deepcopy

from core.models import Track
from services.autotag_rewrite import Candidate, EnrichmentResult
from services.metadata_pipeline_v2 import MetadataPipelineV2
from ui.main_window import _should_refresh_existing_metadata


def test_should_refresh_existing_metadata_defaults_to_incremental(monkeypatch):
    monkeypatch.setattr(
        "ui.main_window.list_metadata_history",
        lambda _path, field_name=None: [{"field": "genre", "old": "", "new": "Trance"}],
    )

    assert _should_refresh_existing_metadata("demo.mp3") is False
    assert _should_refresh_existing_metadata("demo.mp3", force_refresh=False) is False


def test_should_refresh_existing_metadata_only_when_forced():
    assert _should_refresh_existing_metadata("demo.mp3", force_refresh=True) is True


def test_second_pass_keeps_baseline_fields_when_remote_is_weaker():
    """Symulacja drugiego autotagu: baseline ma genre, słabsze API proponuje inne."""
    baseline = Track(path="demo.mp3", title="Song", artist="Artist", genre="Trance", year="2020")
    candidate = deepcopy(baseline)
    enrichment = EnrichmentResult(
        candidates=[
            Candidate(source="Deezer", score=52, genre="Electronic", year="2019"),
        ],
        best_match=Candidate(source="Deezer", score=52, genre="Electronic", year="2019"),
    )

    result = MetadataPipelineV2().resolve_track(
        baseline_track=baseline,
        candidate_track=candidate,
        enrichment_result=enrichment,
        include_baseline_evidence=True,
    )

    assert result.track.genre == "Trance"
    assert result.track.year == "2020"