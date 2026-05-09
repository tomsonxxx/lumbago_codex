import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6 import QtWidgets

from lumbago_app.core.models import Track
from lumbago_app.services.metadata_writeback import PendingTrackWrite, WritebackResult
from lumbago_app.ui.ai_tagger_dialog import AiTaggerDialog


def test_apply_accepted_persists_placeholder_replacements(monkeypatch, tmp_path: Path):
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    track_path = tmp_path / "demo.mp3"
    track_path.write_bytes(b"ID3")

    original = Track(path=str(track_path), title="\\", artist="unknown")
    dialog = AiTaggerDialog([original], auto_fetch=False, allow_auto_fetch=False)
    state = dialog._states[0]
    state.proposed_track.title = "Fixed Title"
    state.proposed_track.artist = "Fixed Artist"
    state.decisions["title"] = True
    state.decisions["artist"] = True

    calls: dict[str, object] = {}

    def _apply_track_writes(writes, *, max_workers=4, update_mode="bulk"):
        pending: list[PendingTrackWrite] = list(writes)
        calls["writes"] = pending
        return WritebackResult(track_count=len(pending))

    monkeypatch.setattr("lumbago_app.ui.ai_tagger_dialog.apply_track_writes", _apply_track_writes)
    monkeypatch.setattr(dialog, "accept", lambda: calls.__setitem__("accepted", True))

    dialog._apply_accepted()

    assert original.title == "Fixed Title"
    assert original.artist == "Fixed Artist"

    assert "writes" in calls, "_apply_accepted did not call apply_track_writes"
    assert len(calls["writes"]) == 1
    pw: PendingTrackWrite = calls["writes"][0]
    assert pw.track is original
    assert pw.fields == {"title": "Fixed Title", "artist": "Fixed Artist"}

    assert calls.get("accepted") is True

    app.quit()
