"""Testy serwisów integracji (import + smoke tests)."""

import pytest


def test_musicbrainz_service_imports():
    from lumbago_app.services.integrations.musicbrainz_service import MusicBrainzService
    assert MusicBrainzService is not None


def test_discogs_service_imports():
    from lumbago_app.services.integrations.discogs_service import DiscogsService
    assert DiscogsService is not None


def test_spotify_service_imports():
    from lumbago_app.services.integrations.spotify_service import SpotifyService
    assert SpotifyService is not None


def test_metadata_merger_imports():
    from lumbago_app.services.integrations.metadata_merger import MetadataMerger
    assert MetadataMerger is not None


def test_energy_levels_complete():
    """ENERGY_LEVELS zawiera 10 poziomów (1-10)."""
    from lumbago_app.core.constants import ENERGY_LEVELS
    assert len(ENERGY_LEVELS) == 10
    assert 1 in ENERGY_LEVELS
    assert 10 in ENERGY_LEVELS


def test_ai_providers_cost_structure():
    """AI_PROVIDERS_COST ma wymaganą strukturę."""
    from lumbago_app.core.constants import AI_PROVIDERS_COST
    for name, info in AI_PROVIDERS_COST.items():
        assert "model" in info
        assert "input_per_1k" in info
        assert "output_per_1k" in info
        assert "priority" in info
