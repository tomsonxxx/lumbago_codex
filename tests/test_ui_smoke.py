import os

from lumbago_app import main as app_main


def test_ui_smoke(monkeypatch):
    monkeypatch.setenv("LUMBAGO_SAFE_MODE", "1")
    monkeypatch.setenv("LUMBAGO_SMOKE_SECONDS", "1")
    exit_code = app_main.main()
    assert exit_code == 0
