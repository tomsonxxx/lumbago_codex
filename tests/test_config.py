from __future__ import annotations

import json

from core.config import load_settings


def test_load_settings_defaults_validation_policy_to_aggressive(monkeypatch, tmp_path):
    monkeypatch.setenv("APPDATA", str(tmp_path))
    monkeypatch.delenv("VALIDATION_POLICY", raising=False)

    settings = load_settings()

    assert settings.validation_policy == "aggressive"


def test_load_settings_normalizes_invalid_validation_policy(monkeypatch, tmp_path):
    monkeypatch.setenv("APPDATA", str(tmp_path))
    settings_dir = tmp_path / "LumbagoMusicAI"
    settings_dir.mkdir(parents=True, exist_ok=True)
    (settings_dir / "settings.json").write_text(
        json.dumps({"VALIDATION_POLICY": "totally-invalid"}),
        encoding="utf-8",
    )

    settings = load_settings()

    assert settings.validation_policy == "aggressive"
