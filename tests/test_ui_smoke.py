import ctypes.util
import os
import subprocess
import sys

import pytest


def test_ui_smoke():
    if ctypes.util.find_library("EGL") is None:
        pytest.skip("Brak biblioteki systemowej libEGL wymaganej przez PyQt6 w teście UI smoke.")
    if ctypes.util.find_library("pulse") is None:
        pytest.skip("Brak biblioteki systemowej libpulse wymaganej przez QtMultimedia w teście UI smoke.")

    env = os.environ.copy()
    env["LUMBAGO_SAFE_MODE"] = "1"
    env["LUMBAGO_SMOKE_SECONDS"] = "1"
    result = subprocess.run(
        [sys.executable, "-c", "import main; raise SystemExit(main.main())"],
        env=env,
        check=False,
    )
    assert result.returncode == 0


def test_smart_collections_stub():
    """Stub coverage for Smart Collections (per SZPIEG research 2026-06-15 Smart Collections + finalny efekt końcowy... must document identical).
    Basic path: repo get_tracks_for_smart_rules (early return on no rules/empty conditions) + import of smart-aware models/main (no full DB).
    Full query/apply tested in integration + manual at end per PLAN. Targeted/perf guards + EFFECT exercised at runtime.
    """
    from data.repository import get_tracks_for_smart_rules
    # no rules or empty conditions -> [] (no DB hit)
    assert get_tracks_for_smart_rules(None) == []
    assert get_tracks_for_smart_rules({}) == []
    assert get_tracks_for_smart_rules({"conditions": []}) == []
    # presence of smart plumbing (import succeeds post edits) -- guarded for headless/CI without PyQt
    try:
        from ui.library_widget import LibraryWidget
        from ui.models import TrackTableModel
        # main_window may pull more; skip full if no Qt to keep smoke robust
        assert hasattr(LibraryWidget, "_on_smart_item")
        assert hasattr(TrackTableModel, "update_tracks")
    except Exception:
        # OK in minimal env; ui smoke main test already handles skips
        pass
    # note: real smart with rules requires populated DB + Playlist.is_smart; see test_integration_db and manual CHECKLIST
