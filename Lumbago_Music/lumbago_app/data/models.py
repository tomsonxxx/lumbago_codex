"""
Lumbago Music AI — Modele SQLAlchemy 2.0
==========================================
8 modeli ORM dla pełnej biblioteki DJ.
"""

import datetime
import json
import logging
from typing import Optional

from sqlalchemy import (
    Boolean, DateTime, Float, ForeignKey, Index, Integer,
    String, Text, UniqueConstraint, func,
)
from sqlalchemy.orm import (
    DeclarativeBase, Mapped, mapped_column, relationship,
)

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """Bazowa klasa ORM."""
    pass


# ------------------------------------------------------------------ #
# TrackOrm — główny model utworu (29+ pól)
# ------------------------------------------------------------------ #

class TrackOrm(Base):
    """Pełny model utworu muzycznego w bibliotece DJ."""

    __tablename__ = "tracks"

    # Klucz główny
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # --- Ścieżka i identyfikacja ---
    file_path: Mapped[str] = mapped_column(String(1024), unique=True, nullable=False, index=True)
    file_hash: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    file_size: Mapped[Optional[int]] = mapped_column(Integer)
    file_modified: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)

    # --- Metadane podstawowe ---
    title: Mapped[Optional[str]] = mapped_column(String(512))
    artist: Mapped[Optional[str]] = mapped_column(String(512), index=True)
    album: Mapped[Optional[str]] = mapped_column(String(512))
    album_artist: Mapped[Optional[str]] = mapped_column(String(512))
    year: Mapped[Optional[int]] = mapped_column(Integer)
    track_number: Mapped[Optional[int]] = mapped_column(Integer)
    disc_number: Mapped[Optional[int]] = mapped_column(Integer)
    label: Mapped[Optional[str]] = mapped_column(String(256))
    catalog_number: Mapped[Optional[str]] = mapped_column(String(128))
    isrc: Mapped[Optional[str]] = mapped_column(String(20), index=True)

    # --- Analiza audio ---
    duration: Mapped[Optional[float]] = mapped_column(Float)        # sekundy
    bpm: Mapped[Optional[float]] = mapped_column(Float)
    bpm_stable: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    key_musical: Mapped[Optional[str]] = mapped_column(String(32))  # "C major"
    key_camelot: Mapped[Optional[str]] = mapped_column(String(4))   # "8B"
    lufs_integrated: Mapped[Optional[float]] = mapped_column(Float)
    lufs_true_peak: Mapped[Optional[float]] = mapped_column(Float)
    energy_level: Mapped[Optional[int]] = mapped_column(Integer)    # 1-10
    bit_rate: Mapped[Optional[int]] = mapped_column(Integer)        # kbps
    sample_rate: Mapped[Optional[int]] = mapped_column(Integer)     # Hz
    channels: Mapped[Optional[int]] = mapped_column(Integer)
    codec: Mapped[Optional[str]] = mapped_column(String(32))

    # --- Klasyfikacja ---
    genre: Mapped[Optional[str]] = mapped_column(String(128), index=True)
    genre_secondary: Mapped[Optional[str]] = mapped_column(String(128))
    mood: Mapped[Optional[str]] = mapped_column(String(256))        # JSON array
    style: Mapped[Optional[str]] = mapped_column(String(256))

    # --- Oceny i status ---
    rating: Mapped[Optional[int]] = mapped_column(Integer)          # 1-5
    play_count: Mapped[int] = mapped_column(Integer, default=0)
    last_played: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    is_analyzed: Mapped[bool] = mapped_column(Boolean, default=False)
    is_fingerprinted: Mapped[bool] = mapped_column(Boolean, default=False)
    is_missing: Mapped[bool] = mapped_column(Boolean, default=False)
    is_corrupt: Mapped[bool] = mapped_column(Boolean, default=False)

    # --- Zewnętrzne ID ---
    acoustid_id: Mapped[Optional[str]] = mapped_column(String(64))
    musicbrainz_recording_id: Mapped[Optional[str]] = mapped_column(String(64))
    musicbrainz_release_id: Mapped[Optional[str]] = mapped_column(String(64))
    discogs_release_id: Mapped[Optional[str]] = mapped_column(String(32))
    spotify_track_id: Mapped[Optional[str]] = mapped_column(String(32))

    # --- Waveform ---
    waveform_data: Mapped[Optional[str]] = mapped_column(Text)      # JSON compressed peaks

    # --- Timestamps ---
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )

    # --- Relacje ---
    tags: Mapped[list["TagOrm"]] = relationship(
        "TagOrm", back_populates="track", cascade="all, delete-orphan"
    )
    cue_points: Mapped[list["CuePointOrm"]] = relationship(
        "CuePointOrm", back_populates="track",
        cascade="all, delete-orphan", order_by="CuePointOrm.position",
    )
    playlist_entries: Mapped[list["PlaylistTrackOrm"]] = relationship(
        "PlaylistTrackOrm", back_populates="track", cascade="all, delete-orphan"
    )
    change_logs: Mapped[list["ChangeLogOrm"]] = relationship(
        "ChangeLogOrm", back_populates="track", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_tracks_artist_title", "artist", "title"),
        Index("ix_tracks_bpm_key", "bpm", "key_camelot"),
    )

    def __repr__(self) -> str:
        return f"<Track id={self.id} artist={self.artist!r} title={self.title!r}>"

    @property
    def moods(self) -> list[str]:
        """Zwraca listę nastrojów (dekoduje JSON)."""
        if not self.mood:
            return []
        try:
            return json.loads(self.mood)
        except (json.JSONDecodeError, TypeError):
            return [self.mood]

    @moods.setter
    def moods(self, value: list[str]) -> None:
        self.mood = json.dumps(value, ensure_ascii=False)


# ------------------------------------------------------------------ #
# TagOrm — tagi (wiele:wiele przez track_id)
# ------------------------------------------------------------------ #

class TagOrm(Base):
    """Tag przypisany do utworu (może być wiele na utwór)."""

    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    track_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tracks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String(64))     # np. "mood", "genre", "custom"
    source: Mapped[Optional[str]] = mapped_column(String(32))       # "ai", "manual", "import"
    confidence: Mapped[Optional[float]] = mapped_column(Float)      # 0.0 - 1.0

    track: Mapped["TrackOrm"] = relationship("TrackOrm", back_populates="tags")

    __table_args__ = (
        UniqueConstraint("track_id", "name", name="uq_track_tag"),
        Index("ix_tags_name", "name"),
    )

    def __repr__(self) -> str:
        return f"<Tag track_id={self.track_id} name={self.name!r}>"


# ------------------------------------------------------------------ #
# CuePointOrm — punkty cue
# ------------------------------------------------------------------ #

class CuePointOrm(Base):
    """Punkt cue (hot cue, memory cue, loop) dla utworu."""

    __tablename__ = "cue_points"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    track_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tracks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    index: Mapped[int] = mapped_column(Integer, nullable=False)     # 1-8
    position: Mapped[float] = mapped_column(Float, nullable=False)  # sekundy
    label: Mapped[Optional[str]] = mapped_column(String(64))
    color: Mapped[Optional[str]] = mapped_column(String(7))         # "#FF0000"
    cue_type: Mapped[str] = mapped_column(
        String(16), default="hot_cue"
    )   # "hot_cue", "memory", "loop_in", "loop_out"
    loop_out: Mapped[Optional[float]] = mapped_column(Float)        # dla pętli

    track: Mapped["TrackOrm"] = relationship("TrackOrm", back_populates="cue_points")

    __table_args__ = (
        UniqueConstraint("track_id", "index", name="uq_cue_index"),
    )

    def __repr__(self) -> str:
        return f"<CuePoint track_id={self.track_id} idx={self.index} pos={self.position:.2f}>"


# ------------------------------------------------------------------ #
# PlaylistOrm — playlisty (drzewo, self-referential)
# ------------------------------------------------------------------ #

class PlaylistOrm(Base):
    """Playlista lub folder playlist (hierarchia)."""

    __tablename__ = "playlists"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    parent_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("playlists.id", ondelete="CASCADE"), index=True
    )
    is_folder: Mapped[bool] = mapped_column(Boolean, default=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    description: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )

    # Self-referential
    children: Mapped[list["PlaylistOrm"]] = relationship(
        "PlaylistOrm",
        back_populates="parent",
        cascade="all, delete-orphan",
    )
    parent: Mapped[Optional["PlaylistOrm"]] = relationship(
        "PlaylistOrm", back_populates="children", remote_side="PlaylistOrm.id"
    )
    tracks: Mapped[list["PlaylistTrackOrm"]] = relationship(
        "PlaylistTrackOrm", back_populates="playlist",
        cascade="all, delete-orphan", order_by="PlaylistTrackOrm.position",
    )

    def __repr__(self) -> str:
        return f"<Playlist id={self.id} name={self.name!r} folder={self.is_folder}>"


# ------------------------------------------------------------------ #
# PlaylistTrackOrm — relacja playlista-utwór (z pozycją)
# ------------------------------------------------------------------ #

class PlaylistTrackOrm(Base):
    """Wpis utworu w playliście z pozycją kolejkowania."""

    __tablename__ = "playlist_tracks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    playlist_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("playlists.id", ondelete="CASCADE"), nullable=False, index=True
    )
    track_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tracks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    added_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow
    )

    playlist: Mapped["PlaylistOrm"] = relationship("PlaylistOrm", back_populates="tracks")
    track: Mapped["TrackOrm"] = relationship("TrackOrm", back_populates="playlist_entries")

    __table_args__ = (
        UniqueConstraint("playlist_id", "track_id", name="uq_playlist_track"),
    )

    def __repr__(self) -> str:
        return (
            f"<PlaylistTrack pl={self.playlist_id} "
            f"track={self.track_id} pos={self.position}>"
        )


# ------------------------------------------------------------------ #
# ChangeLogOrm — historia zmian metadanych
# ------------------------------------------------------------------ #

class ChangeLogOrm(Base):
    """Historia zmian pola metadanych dla auditu."""

    __tablename__ = "change_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    track_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tracks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    field_name: Mapped[str] = mapped_column(String(64), nullable=False)
    old_value: Mapped[Optional[str]] = mapped_column(Text)
    new_value: Mapped[Optional[str]] = mapped_column(Text)
    changed_by: Mapped[str] = mapped_column(
        String(32), default="user"
    )   # "user", "ai", "import", "musicbrainz"
    changed_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow, index=True
    )

    track: Mapped["TrackOrm"] = relationship("TrackOrm", back_populates="change_logs")

    def __repr__(self) -> str:
        return (
            f"<ChangeLog track={self.track_id} "
            f"field={self.field_name!r} at={self.changed_at}>"
        )


# ------------------------------------------------------------------ #
# MetadataCacheOrm — cache odpowiedzi zewnętrznych serwisów
# ------------------------------------------------------------------ #

class MetadataCacheOrm(Base):
    """Cache odpowiedzi z zewnętrznych API (MusicBrainz, Discogs itp.)."""

    __tablename__ = "metadata_cache"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cache_key: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(32), nullable=False)  # "musicbrainz", "discogs"
    data_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow
    )
    expires_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, index=True)
    hit_count: Mapped[int] = mapped_column(Integer, default=0)

    def __repr__(self) -> str:
        return f"<MetadataCache key={self.cache_key!r} source={self.source!r}>"

    @property
    def is_expired(self) -> bool:
        """Sprawdza czy cache wygasł."""
        if self.expires_at is None:
            return False
        return datetime.datetime.utcnow() > self.expires_at


# ------------------------------------------------------------------ #
# SettingsOrm — ustawienia aplikacji w bazie
# ------------------------------------------------------------------ #

class SettingsOrm(Base):
    """Persystentne ustawienia aplikacji (klucz-wartość)."""

    __tablename__ = "app_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    value: Mapped[Optional[str]] = mapped_column(Text)
    value_type: Mapped[str] = mapped_column(
        String(16), default="str"
    )   # "str", "int", "float", "bool", "json"
    description: Mapped[Optional[str]] = mapped_column(String(256))
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )

    def __repr__(self) -> str:
        return f"<Settings key={self.key!r} value={self.value!r}>"

    def get_typed_value(self) -> object:
        """Zwraca wartość skonwertowaną do właściwego typu."""
        if self.value is None:
            return None
        match self.value_type:
            case "int":
                return int(self.value)
            case "float":
                return float(self.value)
            case "bool":
                return self.value.lower() in ("1", "true", "yes")
            case "json":
                return json.loads(self.value)
            case _:
                return self.value
