"""Testy modeli SQLAlchemy."""

import pytest
from lumbago_app.data.models import TrackOrm, TagOrm, CuePointOrm, PlaylistOrm


def test_track_creation(db_session, sample_track_data):
    """TrackOrm można stworzyć i zapisać."""
    track = TrackOrm(**sample_track_data)
    db_session.add(track)
    db_session.flush()
    assert track.id is not None
    assert track.artist == "Test Artist"


def test_track_moods_property(db_session):
    """Właściwość moods poprawnie serializuje/deserializuje JSON."""
    track = TrackOrm(file_path="/test/moods.mp3")
    track.moods = ["dark", "energetic", "driving"]
    db_session.add(track)
    db_session.flush()
    assert "dark" in track.moods
    assert len(track.moods) == 3


def test_track_tag_relationship(db_session, sample_track_data):
    """TrackOrm.tags relacja działa poprawnie."""
    track = TrackOrm(**sample_track_data)
    track.file_path = "/test/tags_test.mp3"
    tag = TagOrm(name="underground", category="custom", source="manual")
    track.tags.append(tag)
    db_session.add(track)
    db_session.flush()
    assert len(track.tags) == 1
    assert track.tags[0].name == "underground"


def test_playlist_self_referential(db_session):
    """PlaylistOrm self-referential parent-child działa."""
    folder = PlaylistOrm(name="Techno", is_folder=True)
    child = PlaylistOrm(name="Hard Techno", is_folder=False)
    folder.children.append(child)
    db_session.add(folder)
    db_session.flush()
    assert len(folder.children) == 1
    assert child.parent_id == folder.id


def test_settings_typed_value():
    """SettingsOrm.get_typed_value() konwertuje poprawnie."""
    from lumbago_app.data.models import SettingsOrm
    s = SettingsOrm(key="test_int", value="42", value_type="int")
    assert s.get_typed_value() == 42
    s2 = SettingsOrm(key="test_bool", value="true", value_type="bool")
    assert s2.get_typed_value() is True
