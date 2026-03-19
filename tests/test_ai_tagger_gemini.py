from __future__ import annotations

from lumbago_app.core.models import Track
from lumbago_app.services.ai_tagger import CloudAiTagger


class _FakeResponse:
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
    assert ":generateContent" in calls["url"]
    assert result.genre == "house"
    assert result.confidence == 0.8

