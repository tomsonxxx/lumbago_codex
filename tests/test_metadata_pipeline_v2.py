from __future__ import annotations

from copy import deepcopy

from lumbago_app.core.models import Track
from lumbago_app.services.autotag_rewrite import Candidate, EnrichmentResult
from lumbago_app.services.metadata_consensus import FieldEvidence
from lumbago_app.services.metadata_enricher import MetadataFillReport, SourceProbe
from lumbago_app.services.metadata_pipeline_v2 import MetadataPipelineV2
from lumbago_app.services.recognition_pipeline_v2 import RecognitionPipelineResult


def test_pipeline_preserves_existing_artist_against_ai_and_keeps_conflict():
    baseline = Track(path="demo.mp3", title="Children", artist="Tiesto")
    candidate_track = deepcopy(baseline)
    candidate_track.mood = "uplifting"

    enrichment = EnrichmentResult(
        candidates=[
            Candidate(source="AI", score=96, artist="Hardwell", mood="uplifting"),
            Candidate(source="MusicBrainz", score=88, artist="Tiesto"),
        ],
        best_match=Candidate(source="AI", score=96, artist="Hardwell", mood="uplifting"),
    )
    report = MetadataFillReport(
        method="mix",
        changed_fields=["mood"],
        sources=[SourceProbe(key="local_library", label="Biblioteka lokalna", status="hit", fields=["mood"])],
    )

    result = MetadataPipelineV2().resolve_track(
        baseline_track=baseline,
        candidate_track=candidate_track,
        metadata_report=report,
        enrichment_result=enrichment,
    )

    assert result.track.artist == "Tiesto"
    assert result.track.mood == "uplifting"
    assert result.consensus.conflicts
    assert any(conflict.field_name == "artist" for conflict in result.consensus.conflicts)


def test_pipeline_accepts_verified_extra_evidence_over_unverified_remote_match():
    baseline = Track(path="demo.mp3", title="Children", artist="Tiesto")
    candidate_track = deepcopy(baseline)
    enrichment = EnrichmentResult(
        candidates=[
            Candidate(source="MusicBrainz", score=70, artist="Armin van Buuren"),
        ],
        best_match=Candidate(source="MusicBrainz", score=70, artist="Armin van Buuren"),
    )

    result = MetadataPipelineV2().resolve_track(
        baseline_track=baseline,
        candidate_track=candidate_track,
        enrichment_result=enrichment,
        extra_evidence_by_field={
            "artist": [
                {
                    "value": "Armin van Buuren",
                    "source": "acoustid",
                    "confidence": 0.93,
                    "verified": True,
                }
            ]
        },
    )

    assert result.track.artist == "Armin van Buuren"


def test_pipeline_uses_recognition_result_evidence():
    baseline = Track(path="demo.mp3", title="Wrong", artist="Wrong Artist")
    candidate_track = deepcopy(baseline)

    recognition_result = RecognitionPipelineResult(
        track=deepcopy(baseline),
        evidence_by_field={
            "title": [
                FieldEvidence(
                    field_name="title",
                    value="Correct Title",
                    source="acoustid",
                    confidence=0.98,
                    verified=True,
                )
            ],
            "artist": [
                FieldEvidence(
                    field_name="artist",
                    value="Correct Artist",
                    source="acoustid",
                    confidence=0.98,
                    verified=True,
                )
            ],
        },
        attempts=[],
        summary="sources: acoustid",
        primary_source="acoustid",
        filename_query="Correct Artist Correct Title",
    )

    result = MetadataPipelineV2().resolve_track(
        baseline_track=baseline,
        candidate_track=candidate_track,
        recognition_result=recognition_result,
    )

    assert result.track.title == "Correct Title"
    assert result.track.artist == "Correct Artist"


def test_pipeline_can_skip_baseline_evidence_when_refreshing():
    baseline = Track(path="demo.mp3", title="Old Title", artist="Old Artist")
    candidate_track = Track(path="demo.mp3")

    result = MetadataPipelineV2().resolve_track(
        baseline_track=baseline,
        candidate_track=candidate_track,
        include_baseline_evidence=False,
    )

    assert result.track.title is None
    assert result.track.artist is None
