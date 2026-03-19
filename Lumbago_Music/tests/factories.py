"""
Lumbago Music AI — Fabryki testowe (factory-boy)
==================================================
Szybkie tworzenie obiektów ORM na potrzeby testów.
"""

import factory
from factory.alchemy import SQLAlchemyModelFactory

from lumbago_app.data.models import (
    CuePointOrm, PlaylistOrm, TagOrm, TrackOrm,
)


class TrackFactory(SQLAlchemyModelFactory):
    """Fabryka tworzenia TrackOrm dla testów."""

    class Meta:
        model = TrackOrm
        sqlalchemy_session_persistence = "commit"

    file_path = factory.Sequence(lambda n: f"/music/track_{n:04d}.mp3")
    title = factory.Sequence(lambda n: f"Track {n}")
    artist = factory.Faker("name")
    album = factory.Faker("sentence", nb_words=3)
    genre = factory.Iterator(["House", "Techno", "Trance", "DnB"])
    bpm = factory.Faker("pyfloat", min_value=100, max_value=180, right_digits=1)
    key_camelot = factory.Iterator(["8A", "8B", "9A", "9B", "1A"])
    duration = factory.Faker("pyfloat", min_value=180, max_value=600, right_digits=1)
    year = factory.Faker("year")
    rating = factory.Iterator([None, 3, 4, 5])
    energy_level = factory.Faker("random_int", min=1, max=10)
    is_analyzed = False
    is_fingerprinted = False


class TagFactory(SQLAlchemyModelFactory):
    class Meta:
        model = TagOrm
        sqlalchemy_session_persistence = "commit"

    name = factory.Faker("word")
    category = "manual"
    source = "manual"
    confidence = 1.0


class PlaylistFactory(SQLAlchemyModelFactory):
    class Meta:
        model = PlaylistOrm
        sqlalchemy_session_persistence = "commit"

    name = factory.Sequence(lambda n: f"Playlist {n}")
    is_folder = False
