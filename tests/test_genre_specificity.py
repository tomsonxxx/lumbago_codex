from __future__ import annotations

from services.genre_specificity import (
    is_broad_genre,
    pick_most_specific_genre,
    should_upgrade_genre,
)
from services.metadata_consensus import FieldEvidence, MetadataConsensusEngine


def test_is_broad_genre_detects_generic_labels():
    assert is_broad_genre("Electronic") is True
    assert is_broad_genre("Dance") is True
    assert is_broad_genre("Deep House") is False
    assert is_broad_genre("Melodic Techno") is False


def test_pick_most_specific_genre_prefers_subgenre():
    best = pick_most_specific_genre(
        ["Electronic", "Dance", "Deep House", "House"],
        current="Dance",
    )
    assert best == "Deep House"


def test_should_upgrade_genre_from_broad_to_specific():
    assert should_upgrade_genre("Electronic", "Progressive Trance") is True
    assert should_upgrade_genre("Deep House", "House") is False


def test_consensus_prefers_specific_genre_over_broad_existing_tag():
    engine = MetadataConsensusEngine()
    report = engine.resolve(
        {
            "genre": [
                FieldEvidence(
                    field_name="genre",
                    value="Dance",
                    source="existing_tags",
                    confidence=0.9,
                ),
                FieldEvidence(
                    field_name="genre",
                    value="Melodic Techno",
                    source="ai_enrichment",
                    confidence=0.82,
                ),
                FieldEvidence(
                    field_name="genre",
                    value="Techno",
                    source="deezer_tag",
                    confidence=0.7,
                ),
            ]
        }
    )

    genre = report.fields["genre"]
    assert genre.resolved is not None
    assert genre.resolved.value == "Melodic Techno"