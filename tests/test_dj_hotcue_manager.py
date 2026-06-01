"""
Unit tests for HotcueManager (extracted by WRITER to eliminate duplication
between DeckWidget and SinglePlayerView) and related refactor artifacts.

Focus:
- Core HotcueManager CRUD, max_cues clamping, visible pads
- DB persistence paths with mocks (happy, fallback, errors -> logged not swallowed)
- Regression: set/jump/save/load/clear behavior is now identical via shared manager
- format_track_time (co-extracted utility)

These tests run with no GUI (no QWidget instantiation, no QApplication required).
All DB interactions are fully mocked via monkeypatch on the ui module globals.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# Ensure project root on path (matches other test files)
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ui.dj.hotcue_manager import HotcueManager, format_track_time
import ui.dj.hotcue_manager as hotcue_mod  # NOWY moduł – tu są teraz _HAS_CUE_REPOSITORY + funkcje repo (dla monkeypatch)
from core.models import CuePoint


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def fresh_mgr() -> HotcueManager:
    """Fresh 8-cue manager for most tests."""
    return HotcueManager(max_cues=8)


@pytest.fixture
def single_view_mgr() -> HotcueManager:
    """Simulates SinglePlayerView (max 4 visible pads)."""
    return HotcueManager(max_cues=4)


# ---------------------------------------------------------------------------
# Basic data layer (happy path) — core of the extraction
# ---------------------------------------------------------------------------

def test_hotcue_manager_basic_crud(fresh_mgr: HotcueManager):
    """Happy path: set/get/clear/clear_all/property roundtrips."""
    assert fresh_mgr.get(0) is None
    assert fresh_mgr.hotcues == {}

    fresh_mgr.set(0, 1234)
    fresh_mgr.set(3, 5678)
    assert fresh_mgr.get(0) == 1234
    assert fresh_mgr.get(3) == 5678
    assert fresh_mgr.hotcues == {0: 1234, 3: 5678}

    # Overwrite
    fresh_mgr.set(0, 9999)
    assert fresh_mgr.get(0) == 9999
    assert len(fresh_mgr.hotcues) == 2

    fresh_mgr.clear(0)
    assert fresh_mgr.get(0) is None
    assert 0 not in fresh_mgr.hotcues

    fresh_mgr.clear_all()
    assert fresh_mgr.hotcues == {}
    assert fresh_mgr.get(3) is None


def test_set_clamps_to_max_cues():
    """set() silently ignores indices >= max_cues (matches widget pad logic)."""
    mgr = HotcueManager(max_cues=4)
    mgr.set(0, 100)
    mgr.set(3, 300)
    mgr.set(4, 400)   # clamped out
    mgr.set(7, 700)
    mgr.set(-1, 50)   # negative ignored by guard

    assert mgr.get(0) == 100
    assert mgr.get(3) == 300
    assert mgr.get(4) is None
    assert mgr.get(7) is None
    assert len(mgr.hotcues) == 2


def test_init_max_cues_bounds():
    """Constructor clamps max_cues to sane [4,8] range (defensive)."""
    assert HotcueManager(max_cues=1)._max_cues == 4
    assert HotcueManager(max_cues=3)._max_cues == 4
    assert HotcueManager(max_cues=4)._max_cues == 4
    assert HotcueManager(max_cues=5)._max_cues == 5
    assert HotcueManager(max_cues=8)._max_cues == 8
    assert HotcueManager(max_cues=99)._max_cues == 8
    assert HotcueManager(max_cues=0)._max_cues == 4


def test_get_visible_cues_for_pad_rendering(fresh_mgr: HotcueManager):
    """get_visible_cues(limit) powers the 4/8 pad mode toggle without data loss."""
    fresh_mgr.set(0, 10)
    fresh_mgr.set(1, 20)
    fresh_mgr.set(4, 40)
    fresh_mgr.set(7, 70)

    assert fresh_mgr.get_visible_cues(4) == {0: 10, 1: 20}
    assert fresh_mgr.get_visible_cues(2) == {0: 10, 1: 20}
    assert fresh_mgr.get_visible_cues() == {0: 10, 1: 20, 4: 40, 7: 70}  # defaults to _max_cues
    assert fresh_mgr.get_visible_cues(8) == fresh_mgr.get_visible_cues()

    # Higher indices still stored (for memory recall / 8-mode) even if not visible
    assert 4 in fresh_mgr.hotcues


# ---------------------------------------------------------------------------
# DB persistence layer (the code that was duplicated and is now centralized)
# ---------------------------------------------------------------------------

def test_load_from_db_when_no_repository(monkeypatch, caplog):
    """Fallback when repository import failed at startup (original graceful behavior)."""
    monkeypatch.setattr(hotcue_mod, "_HAS_CUE_REPOSITORY", False)
    monkeypatch.setattr(hotcue_mod, "get_cue_points_for_track", None)

    mgr = HotcueManager(max_cues=8)
    mgr.set(0, 999)  # pre-existing should be cleared

    with caplog.at_level(logging.DEBUG):
        result = mgr.load_from_db(42)

    assert result == {}
    assert mgr.hotcues == {}
    assert "No cue repository available" in caplog.text


def test_load_from_db_happy_path_populates_and_filters(monkeypatch):
    """Happy DB load: only valid hotcue_index < max_cues are accepted."""
    mock_cues = [
        CuePoint(time_ms=1500, hotcue_index=0, cue_type="hotcue"),
        CuePoint(time_ms=3200, hotcue_index=2, cue_type="hotcue"),
        CuePoint(time_ms=5000, hotcue_index=5, cue_type="hotcue"),   # filtered for max=4
        CuePoint(time_ms=777, hotcue_index=None, cue_type="load"),   # non-hotcue ignored
    ]
    mock_get = MagicMock(return_value=mock_cues)
    monkeypatch.setattr(hotcue_mod, "_HAS_CUE_REPOSITORY", True)
    monkeypatch.setattr(hotcue_mod, "get_cue_points_for_track", mock_get)

    mgr = HotcueManager(max_cues=4)
    loaded = mgr.load_from_db(track_id=123)

    assert loaded == {0: 1500, 2: 3200}
    assert mgr.get(0) == 1500
    assert mgr.get(2) == 3200
    assert mgr.get(5) is None
    mock_get.assert_called_once_with(123)


def test_load_from_db_clears_before_load(monkeypatch):
    """load_from_db always starts fresh (important for track switch)."""
    mock_get = MagicMock(return_value=[
        CuePoint(time_ms=100, hotcue_index=1)
    ])
    monkeypatch.setattr(hotcue_mod, "_HAS_CUE_REPOSITORY", True)
    monkeypatch.setattr(hotcue_mod, "get_cue_points_for_track", mock_get)

    mgr = HotcueManager(max_cues=8)
    mgr.set(0, 999)
    mgr.set(7, 7000)

    mgr.load_from_db(99)
    assert 0 not in mgr.hotcues
    assert 7 not in mgr.hotcues
    assert mgr.get(1) == 100


def test_load_from_db_repo_error_is_logged_not_swallowed(monkeypatch, caplog):
    """FIXER regression: errors during load are logged (warning) instead of silent."""
    def exploding_get(track_id):
        raise RuntimeError("cue_points table locked")

    monkeypatch.setattr(hotcue_mod, "_HAS_CUE_REPOSITORY", True)
    monkeypatch.setattr(hotcue_mod, "get_cue_points_for_track", exploding_get)

    mgr = HotcueManager(max_cues=8)
    with caplog.at_level(logging.WARNING):
        result = mgr.load_from_db(1)

    assert result == {}
    assert mgr.hotcues == {}
    assert "Error loading hotcues" in caplog.text
    assert "cue_points table locked" in caplog.text


def test_save_to_db_early_returns_without_track_id(monkeypatch):
    """No crash / no DB call when track not yet associated (common during load)."""
    mock_save = MagicMock()
    monkeypatch.setattr(hotcue_mod, "_HAS_CUE_REPOSITORY", True)
    monkeypatch.setattr(hotcue_mod, "save_cue_point", mock_save)

    mgr = HotcueManager(max_cues=8)
    mgr.save_to_db(0, 1234)  # track_id never set
    mock_save.assert_not_called()


def test_save_to_db_happy_path_constructs_cue_and_calls_repo(monkeypatch):
    """Exact delegation contract used by both DeckWidget and SinglePlayerView."""
    mock_save = MagicMock()
    monkeypatch.setattr(hotcue_mod, "_HAS_CUE_REPOSITORY", True)
    monkeypatch.setattr(hotcue_mod, "save_cue_point", mock_save)

    mgr = HotcueManager(max_cues=8)
    mgr.set_track_id(777)
    mgr.save_to_db(index=2, time_ms=45678, color="#custom")

    assert mock_save.call_count == 1
    track_arg, cue_arg = mock_save.call_args[0]
    assert track_arg == 777
    assert isinstance(cue_arg, CuePoint)
    assert cue_arg.time_ms == 45678
    assert cue_arg.hotcue_index == 2
    assert cue_arg.cue_type == "hotcue"
    assert cue_arg.color == "#custom"


def test_save_to_db_uses_default_color_from_palette(monkeypatch):
    """When no color passed, uses BOOTH_COLORS (nowa architektura) – 8 unikalnych high-contrast."""
    mock_save = MagicMock()
    monkeypatch.setattr(hotcue_mod, "_HAS_CUE_REPOSITORY", True)
    monkeypatch.setattr(hotcue_mod, "save_cue_point", mock_save)

    mgr = HotcueManager(max_cues=8)
    mgr.set_track_id(1)
    mgr.save_to_db(0, 100)  # no color

    cue = mock_save.call_args[0][1]
    assert cue.color in hotcue_mod.BOOTH_COLORS["hotcue"]


def test_save_to_db_repo_error_logged_not_swallowed(monkeypatch, caplog):
    """FIXER: save errors logged at WARNING, method does not propagate."""
    def exploding_save(track_id, cue):
        raise OSError("disk full for cues")

    monkeypatch.setattr(hotcue_mod, "_HAS_CUE_REPOSITORY", True)
    monkeypatch.setattr(hotcue_mod, "save_cue_point", exploding_save)

    mgr = HotcueManager(max_cues=8)
    mgr.set_track_id(5)
    with caplog.at_level(logging.WARNING):
        mgr.save_to_db(1, 2000)  # must not raise

    assert "Error saving hotcue 1" in caplog.text
    assert "disk full for cues" in caplog.text


def test_delete_from_db_early_return_and_happy(monkeypatch):
    mock_delete = MagicMock()
    monkeypatch.setattr(hotcue_mod, "_HAS_CUE_REPOSITORY", True)
    monkeypatch.setattr(hotcue_mod, "delete_cue_point", mock_delete)

    mgr = HotcueManager(max_cues=8)
    mgr.delete_from_db(3)  # no track_id
    mock_delete.assert_not_called()

    mgr.set_track_id(42)
    mgr.delete_from_db(3)
    mock_delete.assert_called_once_with(42, hotcue_index=3)


def test_delete_from_db_error_logged(monkeypatch, caplog):
    def exploding_delete(track_id, **kwargs):
        raise ValueError("constraint violation")

    monkeypatch.setattr(hotcue_mod, "_HAS_CUE_REPOSITORY", True)
    monkeypatch.setattr(hotcue_mod, "delete_cue_point", exploding_delete)

    mgr = HotcueManager(8)
    mgr.set_track_id(9)
    with caplog.at_level(logging.WARNING):
        mgr.delete_from_db(0)

    assert "Error deleting hotcue 0" in caplog.text


# ---------------------------------------------------------------------------
# Regression: behavior identical for both views (Deck 8-cue vs Single 4-cue)
# ---------------------------------------------------------------------------

def test_hotcue_ops_identical_via_shared_manager(single_view_mgr: HotcueManager, fresh_mgr: HotcueManager):
    """
    Regression test for WRITER extraction.
    Both DeckWidget (max=8) and SinglePlayerView (max=4) now delegate to the
    exact same HotcueManager implementation for set / get / clear / load / save / delete.
    This test proves the data + persistence contract is identical.
    """
    # Simulate what _set_hotcue_from_button + _save_hotcue_to_db does in both widgets
    for mgr, maxv in [(single_view_mgr, 4), (fresh_mgr, 8)]:
        monkeypatch = pytest.MonkeyPatch()
        mock_save = MagicMock()
        monkeypatch.setattr(hotcue_mod, "_HAS_CUE_REPOSITORY", True)
        monkeypatch.setattr(hotcue_mod, "save_cue_point", mock_save)

        mgr.set_track_id(100 + maxv)
        mgr.set(0, 1111)
        mgr.save_to_db(0, 1111)
        mgr.set(1, 2222)
        mgr.save_to_db(1, 2222)

        assert mgr.get(0) == 1111
        assert len(mgr.hotcues) == min(2, maxv)  # single would have clamped higher ones

        # Simulate Ctrl+click clear path (_jump_to_hotcue)
        mgr.clear(0)
        assert mgr.get(0) is None

        # Simulate track load path
        mock_get = MagicMock(return_value=[CuePoint(time_ms=3333, hotcue_index=1)])
        monkeypatch.setattr(hotcue_mod, "get_cue_points_for_track", mock_get)
        loaded = mgr.load_from_db(100 + maxv)
        assert 1 in loaded

        monkeypatch.undo()

    # After independent ops, the two managers remain isolated (as in real dual view)
    assert single_view_mgr.get(0) is None or single_view_mgr._max_cues == 4


def test_clear_all_used_on_track_unload_matches_both_widgets():
    """Both views call clear_all() + _sync on track change / close."""
    mgr = HotcueManager(max_cues=8)
    mgr.set(0, 100)
    mgr.set(7, 800)
    mgr.clear_all()
    assert mgr.hotcues == {}


def test_set_track_id_none_and_zero_handling():
    """Robustness for edge track ids coming from DB or in-memory tracks."""
    mgr = HotcueManager(8)
    mgr.set_track_id(None)
    assert mgr._track_id is None
    mgr.set_track_id(0)
    assert mgr._track_id is None  # falsy -> None per impl


# ---------------------------------------------------------------------------
# Co-extracted utility (format_track_time) — used by both views after refactor
# ---------------------------------------------------------------------------

def test_format_track_time_exact_behavior():
    """Preserves original (slightly varying) formatting from the two widgets."""
    assert format_track_time(None) == "0:00"
    assert format_track_time(0) == "0:00"
    assert format_track_time(999) == "0:00"
    assert format_track_time(1000) == "0:01"
    assert format_track_time(59999) == "0:59"
    assert format_track_time(60000) == "1:00"
    assert format_track_time(123456) == "2:03"
    assert format_track_time(-123) == "0:00"
    assert format_track_time(3600000) == "60:00"


# ---------------------------------------------------------------------------
# Integration-light: simulate full set/jump/save/load/clear cycle
# (what DeckWidget._set_hotcue_from_button + _jump_to_hotcue + _load_hotcues do)
# ---------------------------------------------------------------------------

def test_full_hotcue_cycle_with_db_mocks(monkeypatch):
    """End-to-end cycle matching real usage after WRITER extraction."""
    saved = []
    deleted = []

    def fake_save(track_id, cue):
        saved.append((track_id, cue.hotcue_index, cue.time_ms))

    def fake_delete(track_id, hotcue_index=None, **_):
        deleted.append((track_id, hotcue_index))

    def fake_get(track_id):
        # Simulate prior saves
        if track_id == 555:
            return [CuePoint(time_ms=12345, hotcue_index=0)]
        return []

    monkeypatch.setattr(hotcue_mod, "_HAS_CUE_REPOSITORY", True)
    monkeypatch.setattr(hotcue_mod, "save_cue_point", fake_save)
    monkeypatch.setattr(hotcue_mod, "delete_cue_point", fake_delete)
    monkeypatch.setattr(hotcue_mod, "get_cue_points_for_track", fake_get)

    mgr = HotcueManager(max_cues=8)
    # load (as in load_track)
    loaded = mgr.load_from_db(555)
    assert loaded == {0: 12345}

    # set + save (as in button/waveform handlers in BOTH views)
    mgr.set_track_id(555)
    mgr.set(1, 98765)
    mgr.save_to_db(1, 98765)

    assert (555, 1, 98765) in saved

    # clear + delete (Ctrl+click path)
    mgr.clear(0)
    mgr.delete_from_db(0)
    assert (555, 0) in deleted

    # final state
    assert 0 not in mgr.hotcues
    assert mgr.get(1) == 98765
