from __future__ import annotations

from pathlib import Path

from ui.file_track_ops import _normalize_paths


def test_normalize_paths_deduplicates():
    paths = [Path("a.mp3"), "a.mp3", Path("b.mp3")]
    result = _normalize_paths(paths)
    assert len(result) == 2
    assert result[0] == Path("a.mp3")
    assert result[1] == Path("b.mp3")