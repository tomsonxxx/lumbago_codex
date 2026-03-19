"""Testy AI Tagger i LLM Router."""

import pytest
from unittest.mock import MagicMock, patch


def test_base_provider_parse_response():
    """BaseProvider._parse_response() parsuje poprawny JSON."""
    from lumbago_app.services.ai.providers.base_provider import BaseProvider

    # Concrete subclass for testing
    class MockProvider(BaseProvider):
        provider_name = "mock"
        def tag_tracks(self, t): return {}
        def is_available(self): return True

    p = MockProvider(api_key="key", model="model")
    result = p._parse_response(
        '{"results": [{"id": 1, "genre": "Techno", "mood": ["dark"], '
        '"style": "hard", "energy_level": 8, "tags": ["underground"], "confidence": 0.9}]}'
    )
    assert result[1]["genre"] == "Techno"
    assert result[1]["energy_level"] == 8


def test_base_provider_parse_invalid_json():
    """BaseProvider._parse_response() rzuca LLMResponseError dla złego JSON."""
    from lumbago_app.services.ai.providers.base_provider import BaseProvider
    from lumbago_app.core.exceptions import LLMResponseError

    class MockProvider(BaseProvider):
        provider_name = "mock"
        def tag_tracks(self, t): return {}
        def is_available(self): return True

    p = MockProvider(api_key="key", model="model")
    with pytest.raises(LLMResponseError):
        p._parse_response("To nie jest JSON")


def test_cost_router_no_providers():
    """CostRouter.tag_tracks() rzuca NoProviderAvailableError gdy brak kluczy."""
    import os
    with patch.dict(os.environ, {
        "OPENAI_API_KEY": "", "ANTHROPIC_API_KEY": "",
        "GROK_API_KEY": "", "DEEPSEEK_API_KEY": "", "GEMINI_API_KEY": "",
    }):
        from lumbago_app.services.ai.llm_router import CostRouter
        from lumbago_app.core.exceptions import NoProviderAvailableError

        router = CostRouter()
        with pytest.raises(NoProviderAvailableError):
            router.tag_tracks([{"id": 1, "title": "Test"}])


def test_camelot_wheel_completeness():
    """CAMELOT_WHEEL zawiera 24 tonacje (12 dur + 12 moll)."""
    from lumbago_app.core.constants import CAMELOT_WHEEL
    assert len(CAMELOT_WHEEL) >= 24
    # Sprawdź obecność reprezentatywnych tonacji
    assert "C major" in CAMELOT_WHEEL
    assert "A minor" in CAMELOT_WHEEL
    assert CAMELOT_WHEEL["C major"] == "8B"
    assert CAMELOT_WHEEL["A minor"] == "8A"
