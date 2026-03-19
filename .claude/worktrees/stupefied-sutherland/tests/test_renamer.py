from pathlib import Path
import tempfile

from lumbago_app.core.models import Track
from lumbago_app.core.renamer import build_rename_plan


def test_build_rename_plan_detects_conflict():
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        a = base / "a.mp3"
        b = base / "b.mp3"
        a.write_text("x", encoding="utf-8")
        b.write_text("y", encoding="utf-8")
        tracks = [
            Track(path=str(a), artist="Artist", title="Title"),
            Track(path=str(b), artist="Artist", title="Title"),
        ]
        plan = build_rename_plan(tracks, "{artist} - {title}")
        assert plan[0].conflict is False
        assert plan[1].conflict is True
