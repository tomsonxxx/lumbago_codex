from __future__ import annotations

from lumbago_app.services.metadata_consensus import (
    FieldEvidence,
    MetadataConsensusEngine,
)


def test_consensus_prefers_verified_fingerprint_over_ai_artist_guess():
    engine = MetadataConsensusEngine()

    report = engine.resolve(
        {
            "artist": [
                FieldEvidence(field_name="artist", value="Hardwell", source="ai_enrichment", confidence=0.97),
                FieldEvidence(
                    field_name="artist",
                    value="Armin van Buuren",
                    source="acoustid",
                    confidence=0.86,
                    verified=True,
                ),
            ]
        }
    )

    artist = report.fields["artist"]
    assert artist.resolved is not None
    assert artist.resolved.value == "Armin van Buuren"
    assert artist.conflict is not None
    assert {candidate.value for candidate in artist.conflict.candidates} == {
        "Hardwell",
        "Armin van Buuren",
    }


def test_consensus_rejects_ai_release_year_without_non_ai_corroboration():
    engine = MetadataConsensusEngine()

    report = engine.resolve(
        {
            "year": [
                FieldEvidence(field_name="year", value="2024", source="ai_enrichment", confidence=0.99),
            ]
        }
    )

    year = report.fields["year"]
    assert year.resolved is None
    assert "year" in report.rejected_fields


def test_consensus_allows_ai_enrichment_for_mood_when_no_harder_source_exists():
    engine = MetadataConsensusEngine()

    report = engine.resolve(
        {
            "mood": [
                FieldEvidence(field_name="mood", value="peak time", source="ai_enrichment", confidence=0.74),
            ]
        }
    )

    mood = report.fields["mood"]
    assert mood.resolved is not None
    assert mood.resolved.value == "peak time"
    assert "mood" in report.accepted_fields
