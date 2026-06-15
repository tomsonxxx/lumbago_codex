from __future__ import annotations

from services.metadata_consensus import (
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


def test_consensus_prefers_existing_tags_over_weak_competing_remote():
    engine = MetadataConsensusEngine()

    report = engine.resolve(
        {
            "genre": [
                FieldEvidence(
                    field_name="genre",
                    value="Trance",
                    source="existing_tags",
                    confidence=0.9,
                ),
                FieldEvidence(
                    field_name="genre",
                    value="Dance",
                    source="deezer",
                    confidence=0.55,
                ),
            ]
        }
    )

    genre = report.fields["genre"]
    assert genre.resolved is not None
    assert genre.resolved.value == "Trance"
    assert genre.resolved.source == "existing_tags"


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
