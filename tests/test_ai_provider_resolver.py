from __future__ import annotations

from types import SimpleNamespace

from services.ai_provider_resolver import (
    _candidate_models_for_probe,
    _parse_openai_compatible_models,
    _pick_model,
    cleared_legacy_ai_settings,
    format_api_error_message,
    is_model_not_found_error,
    is_valid_model_hint,
    resolve_ai_provider,
    resolve_ai_provider_with_detail,
    resolve_provider_triplet,
)


def test_is_valid_model_hint_rejects_human_readable_names():
    assert is_valid_model_hint("Grok 4.3") is False
    assert is_valid_model_hint("gpt 4.1 mini") is False
    assert is_valid_model_hint("") is False
    assert is_valid_model_hint(None) is False


def test_is_valid_model_hint_accepts_api_ids():
    assert is_valid_model_hint("grok-2-latest") is True
    assert is_valid_model_hint("gemini-2.0-flash") is True
    assert is_valid_model_hint("gpt-4.1-mini") is True


def test_format_api_error_message_polishes_insufficient_balance():
    msg = format_api_error_message("deepseek", 402, "Insufficient Balance")
    assert "saldo" in msg.lower() or "środk" in msg.lower()
    assert "DeepSeek" in msg
    assert "platform.deepseek.com" in msg


def test_format_api_error_message_polishes_invalid_api_key():
    msg = format_api_error_message("openai", 401, "Incorrect API key provided")
    assert "klucz" in msg.lower()
    assert "OpenAI" in msg


def test_is_model_not_found_error_detects_grok_message():
    exc = Exception(
        'Cloud AI error: 400 Bad Request — {"error":"Model not found: Grok 4.3"}'
    )
    assert is_model_not_found_error(exc) is True
    assert is_model_not_found_error(Exception("timeout")) is False


def test_pick_model_ignores_invalid_hint_and_uses_preferred():
    available = ["grok-beta", "grok-2-latest", "grok-3-mini"]
    model, source = _pick_model("grok", available, "Grok 4.3")
    assert model == "grok-2-latest"
    assert source == "preferred"


def test_pick_model_fuzzy_matches_gemini_revision_suffix():
    available = ["gemini-2.0-flash-001", "gemini-1.5-pro-latest"]
    model, source = _pick_model("gemini", available, None)
    assert model == "gemini-2.0-flash-001"
    assert source == "preferred_fuzzy"


def test_candidate_models_include_preferred_when_api_list_empty():
    candidates, _source, _primary = _candidate_models_for_probe("openai", [], None)
    assert candidates[0] == "gpt-4o-mini"
    assert "gpt-4o" in candidates
    assert len(candidates) >= 4


def test_pick_model_honors_valid_hint():
    available = ["grok-beta", "grok-2-latest"]
    model, source = _pick_model("grok", available, "grok-beta")
    assert model == "grok-beta"
    assert source == "configured_valid"


def test_parse_openai_compatible_models_skips_embeddings():
    payload = {
        "data": [
            {"id": "text-embedding-3-small"},
            {"id": "grok-2-latest"},
            {"id": "whisper-1"},
        ]
    }
    assert _parse_openai_compatible_models(payload) == ["grok-2-latest"]


def test_cleared_legacy_ai_settings_removes_manual_fields():
    cleared = cleared_legacy_ai_settings()
    assert cleared["GROK_MODEL"] == ""
    assert cleared["GEMINI_BASE_URL"] == ""
    assert len(cleared) == 8


def test_resolve_provider_triplet_ignores_invalid_saved_model(monkeypatch):
    settings = SimpleNamespace(
        grok_api_key="xai-test",
        grok_base_url="",
        grok_model="Grok 4.3",
        cloud_ai_api_key="",
        gemini_api_key="",
        gemini_base_url="",
        gemini_model="",
        openai_api_key="",
        openai_base_url="",
        openai_model="",
        deepseek_api_key="",
        deepseek_base_url="",
        deepseek_model="",
    )

    monkeypatch.setattr(
        "services.ai_provider_resolver.resolve_ai_provider",
        lambda *args, **kwargs: SimpleNamespace(
            base_url="https://api.x.ai/v1",
            model="grok-2-latest",
        ),
    )

    api_key, base_url, model = resolve_provider_triplet("grok", settings)
    assert api_key == "xai-test"
    assert base_url == "https://api.x.ai/v1"
    assert model == "grok-2-latest"


def test_resolve_ai_provider_tries_next_preferred_when_first_probe_fails(monkeypatch):
    calls: list[str] = []

    class _ListResp:
        status_code = 404

        def json(self):
            return {}

    class _ProbeResp:
        def __init__(self, status_code: int):
            self.status_code = status_code
            self.text = "fail"

        def json(self):
            return {"error": {"message": "model unavailable"}}

    def _fake_get(*args, **kwargs):
        return _ListResp()

    def _fake_post(url, headers=None, params=None, json=None, timeout=None):
        model = json["model"]
        calls.append(model)
        status = 200 if model == "gpt-4o" else 400
        return _ProbeResp(status)

    monkeypatch.setattr("services.ai_provider_resolver.requests.get", _fake_get)
    monkeypatch.setattr("services.ai_provider_resolver.requests.post", _fake_post)

    resolved, error = resolve_ai_provider_with_detail("openai", "sk-test", force_refresh=True)
    assert resolved is not None
    assert resolved.model == "gpt-4o"
    assert "gpt-4o-mini" in calls
    assert error == ""


def test_resolve_ai_provider_caches_success(monkeypatch, tmp_path):
    cache_file = tmp_path / "ai_provider_cache.json"
    monkeypatch.setattr("services.ai_provider_resolver._cache_path", lambda: cache_file)

    class _Resp:
        status_code = 200

        def json(self):
            return {"data": [{"id": "grok-2-latest"}]}

    class _ProbeResp:
        status_code = 200

        def json(self):
            return {"choices": [{"message": {"content": '{"ok": true}'}}]}

    def _fake_get(url, headers=None, params=None, timeout=None):
        return _Resp()

    def _fake_post(url, headers=None, json=None, timeout=None):
        return _ProbeResp()

    monkeypatch.setattr("services.ai_provider_resolver.requests.get", _fake_get)
    monkeypatch.setattr("services.ai_provider_resolver.requests.post", _fake_post)

    resolved = resolve_ai_provider("grok", "secret-key", force_refresh=True)
    assert resolved is not None
    assert resolved.model == "grok-2-latest"
    assert resolved.base_url == "https://api.x.ai/v1"

    calls = {"get": 0, "post": 0}

    def _count_get(*args, **kwargs):
        calls["get"] += 1
        return _Resp()

    def _count_post(*args, **kwargs):
        calls["post"] += 1
        return _ProbeResp()

    monkeypatch.setattr("services.ai_provider_resolver.requests.get", _count_get)
    monkeypatch.setattr("services.ai_provider_resolver.requests.post", _count_post)

    cached = resolve_ai_provider("grok", "secret-key", force_refresh=False)
    assert cached is not None
    assert cached.source == "cache"
    assert calls["get"] == 0
    assert calls["post"] == 0