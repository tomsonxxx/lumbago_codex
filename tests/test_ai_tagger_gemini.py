from __future__ import annotations

from core.models import Track
from services.ai_tagger import CloudAiTagger


class _FakeResponse:
    status_code = 200
    ok = True

    def __init__(self, payload: dict):
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self._payload


def test_gemini_default_base_url_and_model(monkeypatch):
    calls: dict[str, str] = {}

    def _fake_post(url, headers=None, json=None, timeout=None):
        calls["url"] = url
        calls["api_key"] = headers.get("x-goog-api-key", "")
        calls["model_prompt"] = json["contents"][0]["parts"][0]["text"]
        return _FakeResponse(
            {
                "candidates": [
                    {
                        "content": {
                            "parts": [
                                {
                                    "text": '{"genre":"house","confidence":0.8}'
                                }
                            ]
                        }
                    }
                ]
            }
        )

    monkeypatch.setattr("requests.post", _fake_post)
    tagger = CloudAiTagger(provider="gemini", api_key="secret-key")
    track = Track(path="x.mp3", title="Track", artist="Artist")

    result = tagger.analyze(track)

    assert calls["api_key"] == "secret-key"
    assert calls["url"].startswith("https://generativelanguage.googleapis.com/v1beta/models/")
    assert "/models/gemini-2.0-flash:generateContent" in calls["url"]
    assert ":generateContent" in calls["url"]
    assert result.genre == "house"
    assert result.confidence == 0.8


def test_cloud_tagger_infers_confidence_when_response_omits_it(monkeypatch):
    def _fake_post(url, headers=None, json=None, timeout=None):
        return _FakeResponse(
            {
                "choices": [
                    {
                        "message": {
                            "content": '{"genre":"house","bpm":128,"key":"8A"}'
                        }
                    }
                ]
            }
        )

    monkeypatch.setattr("requests.post", _fake_post)
    tagger = CloudAiTagger(
        provider="grok",
        api_key="secret-key",
        base_url="https://example.test/v1",
        model="demo-model",
    )
    track = Track(path="x.mp3", title="Track", artist="Artist")

    result = tagger.analyze(track)

    assert result.genre == "house"
    assert result.bpm == 128.0
    assert result.key == "8A"
    assert result.confidence == 0.75
