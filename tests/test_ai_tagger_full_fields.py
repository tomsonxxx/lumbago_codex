"""Tests for extended AI tagger field coverage."""
from __future__ import annotations

import json

import pytest

from core.models import AnalysisResult, Track
from services.ai_tagger import (
    CloudAiTagger,
    _ALL_AI_FIELDS,
    _build_prompt,
    _missing_fields,
    _normalize_payload,
)
from services.metadata_enricher import MetadataEnricher
from services.ai_tagger_merge import _merge_analysis_into_track


class _FakeResponse:
    status_code = 200
    ok = True

    def __init__(self, payload: dict):
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self._payload


# ---------------------------------------------------------------------------
# _missing_fields
# ---------------------------------------------------------------------------


def test_missing_fields_detects_all_empty_track():
    track = Track(path="x.mp3")
    missing = _missing_fields(track)
    assert "bpm" in missing
    assert "key" in missing
    assert "mood" in missing
    assert "energy" in missing
    assert "genre" in missing
    assert "title" in missing
    assert "artist" in missing
    assert "album" in missing
    assert "year" in missing
    assert "composer" in missing
    assert "isrc" in missing
    assert "publisher" in missing


def test_missing_fields_always_requests_verification_for_populated_fields():
    track = Track(
        path="x.mp3",
        title="Sandstorm",
        artist="Darude",
        album="Before the Storm",
        genre="Trance",
        bpm=136.0,
        key="8A",
        year="1999",
    )
    missing = _missing_fields(track)
    assert "title" in missing
    assert "artist" in missing
    assert "album" in missing
    assert "genre" in missing
    assert "bpm" in missing
    assert "key" in missing
    assert "year" in missing


def test_missing_fields_treats_unknown_as_missing():
    track = Track(path="x.mp3", genre="Unknown", artist="n/a", title="-")
    missing = _missing_fields(track)
    assert "genre" in missing
    assert "artist" in missing
    assert "title" in missing


# ---------------------------------------------------------------------------
# _build_prompt
# ---------------------------------------------------------------------------


def test_build_prompt_lists_missing_fields():
    track = Track(path="x.mp3", title="Sandstorm", artist="Darude")
    missing = _missing_fields(track)
    prompt = _build_prompt(track, missing)
    assert "album" in prompt
    assert "year" in prompt
    assert "composer" in prompt
    assert "Sandstorm" in prompt
    assert "Darude" in prompt


def test_build_prompt_asks_for_known_fields_but_keeps_them_as_context():
    track = Track(path="x.mp3", title="Sandstorm", artist="Darude", genre="Trance")
    missing = _missing_fields(track)
    prompt = _build_prompt(track, missing)
    assert "genre" in missing
    assert "Sandstorm" in prompt
    assert "Darude" in prompt
    assert "Trance" in prompt


def test_build_prompt_includes_all_known_data():
    track = Track(
        path="x.mp3",
        title="Around the World",
        artist="Daft Punk",
        album="Homework",
        year="1997",
        bpm=121.0,
        key="5A",
    )
    missing = _missing_fields(track)
    prompt = _build_prompt(track, missing)
    assert "Around the World" in prompt
    assert "Daft Punk" in prompt
    assert "Homework" in prompt
    assert "1997" in prompt


# ---------------------------------------------------------------------------
# _normalize_payload
# ---------------------------------------------------------------------------


def test_normalize_payload_accepts_all_ai_fields():
    payload = {field: "value" for field in _ALL_AI_FIELDS}
    payload["confidence"] = 0.9
    payload["description"] = "test"
    payload["unknown_field"] = "should be stripped"

    result = _normalize_payload(payload)

    for field in _ALL_AI_FIELDS:
        assert field in result
    assert "confidence" in result
    assert "description" in result
    assert "unknown_field" not in result


# ---------------------------------------------------------------------------
# CloudAiTagger — full field return from API response
# ---------------------------------------------------------------------------


def test_cloud_tagger_returns_all_fields(monkeypatch):
    api_response = {
        "choices": [
            {
                "message": {
                    "content": json.dumps(
                        {
                            "album": "Homework",
                            "albumartist": "Daft Punk",
                            "year": "1997",
                            "composer": "Thomas Bangalter",
                            "genre": "House",
                            "bpm": 121.0,
                            "key": "5A",
                            "mood": "energetic",
                            "energy": 0.8,
                            "publisher": "Virgin Records",
                            "isrc": "GBDCA9700001",
                            "remixer": None,
                            "tracknumber": "1",
                        }
                    )
                }
            }
        ]
    }

    def _fake_post(url, headers=None, json=None, timeout=None):
        return _FakeResponse(api_response)

    monkeypatch.setattr("requests.post", _fake_post)

    tagger = CloudAiTagger(
        provider="grok",
        api_key="test-key",
        base_url="https://example.test/v1",
        model="test-model",
    )
    track = Track(path="x.mp3", title="Around the World", artist="Daft Punk")
    result = tagger.analyze(track)

    assert result.album == "Homework"
    assert result.albumartist == "Daft Punk"
    assert result.year == "1997"
    assert result.composer == "Thomas Bangalter"
    assert result.genre == "House"
    assert result.bpm == 121.0
    assert result.key == "5A"
    assert result.mood == "energetic"
    assert result.energy == 0.8
    assert result.publisher == "Virgin Records"
    assert result.isrc == "GBDCA9700001"
    assert result.tracknumber == "1"
    assert result.remixer is None


# ---------------------------------------------------------------------------
# _merge_analysis_into_track — metadata fill behavior
# ---------------------------------------------------------------------------


def test_merge_fills_missing_metadata_from_ai():
    track = Track(path="x.mp3", title="Around the World", artist="Daft Punk")
    result = AnalysisResult(
        album="Homework",
        year="1997",
        genre="House",
        composer="Thomas Bangalter",
        publisher="Virgin Records",
    )
    _merge_analysis_into_track(track, result)

    assert track.album == "Homework"
    assert track.year == "1997"
    assert track.genre == "House"
    assert track.composer == "Thomas Bangalter"
    assert track.publisher == "Virgin Records"


def test_merge_overwrites_existing_metadata_with_ai_verified_values():
    track = Track(
        path="x.mp3",
        title="Around the World",
        artist="Daft Punk",
        album="Homework",
        year="1997",
        composer="Hand-edited Composer",
    )
    result = AnalysisResult(album="Wrong Album", year="2000", composer="AI Composer")
    _merge_analysis_into_track(track, result)

    assert track.album == "Wrong Album"
    assert track.year == "2000"
    assert track.composer == "AI Composer"


def test_merge_overwrites_unknown_metadata_placeholder():
    track = Track(path="x.mp3", album="unknown", year="-", publisher="n/a")
    result = AnalysisResult(album="Homework", year="1997", publisher="Virgin Records")
    _merge_analysis_into_track(track, result)

    assert track.album == "Homework"
    assert track.year == "1997"
    assert track.publisher == "Virgin Records"


def test_merge_ai_analysis_fields_always_overwrite():
    """bpm, key, mood, energy, genre should always be updated by AI."""
    track = Track(path="x.mp3", genre="Pop", mood="Calm", bpm=100.0, key="1A", energy=0.3)
    result = AnalysisResult(genre="House", mood="Energetic", bpm=128.0, key="8A", energy=0.9)
    _merge_analysis_into_track(track, result)

    assert track.genre == "House"
    assert track.mood == "Energetic"
    assert track.bpm == 128.0
    assert track.key == "8A"
    assert track.energy == 0.9


# ---------------------------------------------------------------------------
# MusicBrainz enricher — full metadata applied
# ---------------------------------------------------------------------------


def test_musicbrainz_enrich_applies_full_metadata(monkeypatch):
    """enrich_from_musicbrainz_search should fill album, year, genre, etc."""
    from services.metadata_enricher import MetadataEnricher

    mb_search_result = {
        "recordings": [
            {
                "id": "fake-recording-id",
                "title": "Sandstorm",
                "artist-credit": [{"name": "Darude"}],
                "isrcs": ["FIUM79900801"],
                "releases": [
                    {
                        "title": "Before the Storm",
                        "date": "1999-11-15",
                        "artist-credit": [{"name": "Darude"}],
                        "label-info": [{"label": {"name": "Neo Records"}}],
                        "media": [],
                    }
                ],
                "tags": [
                    {"name": "trance", "count": 10},
                    {"name": "energetic", "count": 5},
                ],
                "relations": [
                    {"type": "composer", "artist": {"name": "Ville Virtanen"}}
                ],
            }
        ]
    }

    monkeypatch.setattr(
        "services.metadata_enricher.get_metadata_cache",
        lambda key, ttl: None,
    )
    monkeypatch.setattr(
        "services.metadata_enricher.set_metadata_cache",
        lambda key, data, source=None: None,
    )

    class _FakeMBProvider:
        def search_recording(self, query):
            return mb_search_result

    monkeypatch.setattr(
        "services.metadata_enricher.MusicBrainzProvider",
        lambda app: _FakeMBProvider(),
    )
    # Prevent HTTP call for detailed recording
    monkeypatch.setattr(
        "services.metadata_enricher.MetadataEnricher._fetch_musicbrainz_recording",
        lambda self, recording_id: None,
    )

    enricher = MetadataEnricher("LumbagoTest", validation_policy="lenient")
    track = Track(path="sandstorm.mp3", title="Sandstorm", artist="Darude")

    enriched = enricher.enrich_from_musicbrainz_search(track)

    assert enriched is not None
    assert track.album == "Before the Storm"
    assert track.year == "1999"
    assert track.genre == "trance"
    assert track.isrc == "FIUM79900801"
    assert track.publisher == "Neo Records"
    assert track.composer == "Ville Virtanen"
    assert track.mood == "energetic"


def test_musicbrainz_enrich_replaces_noisy_local_title_and_artist(monkeypatch):
    monkeypatch.setattr(
        "services.metadata_enricher.get_metadata_cache",
        lambda key, ttl: None,
    )
    monkeypatch.setattr(
        "services.metadata_enricher.set_metadata_cache",
        lambda key, data, source=None: None,
    )

    class _FakeMBProvider:
        def search_recording(self, query):
            return {
                "recordings": [
                    {
                        "id": "fake-recording-id",
                        "title": "Sandstorm",
                        "artist-credit": [{"name": "Darude"}],
                        "releases": [
                            {
                                "title": "Before the Storm",
                                "date": "1999-11-15",
                                "artist-credit": [{"name": "Darude"}],
                                "label-info": [{"label": {"name": "Neo Records"}}],
                                "media": [],
                            }
                        ],
                        "tags": [{"name": "trance", "count": 10}],
                    }
                ]
            }

    monkeypatch.setattr(
        "services.metadata_enricher.MusicBrainzProvider",
        lambda app: _FakeMBProvider(),
    )
    monkeypatch.setattr(
        "services.metadata_enricher.MetadataEnricher._fetch_musicbrainz_recording",
        lambda self, recording_id: None,
    )

    enricher = MetadataEnricher("LumbagoTest", validation_policy="lenient")
    track = Track(
        path="sandstorm.mp3",
        title="Sandstorm (Official Video) [HD]",
        artist="Darude - Topic",
        album="Sandstorm (Official Video)",
        year="1998",
        genre="unknown",
    )

    enricher.enrich_from_musicbrainz_search(track)

    assert track.title == "Sandstorm"
    assert track.artist == "Darude"
    assert track.album == "Before the Storm"
    assert track.year == "1999"
    assert track.genre == "trance"
