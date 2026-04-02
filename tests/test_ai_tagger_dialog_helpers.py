from lumbago_app.core.models import Track
from lumbago_app.ui.ai_tagger_dialog import _changed_fields, _format_value


def test_format_value_treats_backslash_placeholder_as_empty():
    assert _format_value("title", "\\") == _format_value("title", None)


def test_changed_fields_detects_replacement_of_placeholder_value():
    original = Track(path="x.mp3", title="\\", artist="unknown")
    proposed = Track(path="x.mp3", title="Fixed Title", artist="Fixed Artist")

    changed = _changed_fields(original, proposed)

    assert "title" in changed
    assert "artist" in changed
