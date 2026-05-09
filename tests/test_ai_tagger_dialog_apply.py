import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6 import QtWidgets

from lumbago_app.core.models import Track
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

    def _replace_track_tags(track_path: str, tags: list[str], source: str, confidence):
        calls["replace"] = {
            "track_path": track_path,
            "tags": tags,
            "source": source,
            "confidence": confidence,
        }

    def _write_tags(path: Path, tags: dict[str, str]):
        calls["write"] = {"path": path, "tags": tags}

    def _update_tracks(tracks):
        calls["update"] = list(tracks)

    monkeypatch.setattr("lumbago_app.services.metadata_writeback.replace_track_tags", _replace_track_tags)
    monkeypatch.setattr("lumbago_app.services.metadata_writeback.write_tags", _write_tags)
    monkeypatch.setattr("lumbago_app.services.metadata_writeback.update_tracks", _update_tracks)
    monkeypatch.setattr(dialog, "accept", lambda: calls.__setitem__("accepted", True))

    dialog._apply_accepted()

    assert original.title == "Fixed Title"
    assert original.artist == "Fixed Artist"
    assert calls["replace"]["tags"] == ["title:Fixed Title", "artist:Fixed Artist"]
    assert calls["write"]["path"] == track_path
    assert calls["write"]["tags"] == {"title": "Fixed Title", "artist": "Fixed Artist"}
    assert calls["update"] == [original]
    assert calls["accepted"] is True

    app.quit()
