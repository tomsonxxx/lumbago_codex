from __future__ import annotations

from core.models import Track
from services.autotag_rewrite import Candidate, EnrichmentResult, UnifiedAutoTagger


def _settings():
    class S:
        provider_parallel_workers = 4
        cloud_ai_provider = ""
        cloud_ai_api_key = None
        openai_api_key = None
        gemini_api_key = None
        grok_api_key = None
        deepseek_api_key = None

    return S()


def test_apply_background_fields_merges_secondary_candidates():
    service = UnifiedAutoTagger(_settings())
    track = Track(path="x.mp3", title="Song", artist="Artist", lyrics=None, remixer=None)
    primary = Candidate(source="MusicBrainz", score=92, comment="Main comment")
    secondary = Candidate(source="LRCLIB", score=48, lyrics="Line one\nLine two")
    tertiary = Candidate(source="Discogs", score=70, remixer="DJ Mix")
    result = EnrichmentResult(
        candidates=[primary, secondary, tertiary],
        best_match=primary,
    )

    changes = service.apply_background_fields(track, result)

    assert changes["lyrics"] == "Line one\nLine two"
    assert changes["remixer"] == "DJ Mix"
    assert changes["comment"] == "Main comment"
    assert track.lyrics == "Line one\nLine two"
    assert track.remixer == "DJ Mix"


def test_apply_background_fields_skips_already_filled():
    service = UnifiedAutoTagger(_settings())
    track = Track(path="x.mp3", title="Song", lyrics="Existing")
    result = EnrichmentResult(
        candidates=[Candidate(source="LRCLIB", score=50, lyrics="New lyrics")],
        best_match=Candidate(source="LRCLIB", score=50, lyrics="New lyrics"),
    )

    changes = service.apply_background_fields(track, result, already_filled_fields={"lyrics"})

    assert changes == {}
    assert track.lyrics == "Existing"