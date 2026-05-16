from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    LargeBinary,
    String,
    Text,
    func,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class TrackOrm(Base):
    __tablename__ = "tracks"
    __table_args__ = (
        Index("ix_tracks_artist", "artist"),
        Index("ix_tracks_title", "title"),
        Index("ix_tracks_album", "album"),
        Index("ix_tracks_year", "year"),
        Index("ix_tracks_genre", "genre"),
        Index("ix_tracks_key", "key"),
        Index("ix_tracks_bpm", "bpm"),
        CheckConstraint("rating >= 0 AND rating <= 5", name="ck_tracks_rating_range"),
        CheckConstraint("bpm IS NULL OR bpm >= 0", name="ck_tracks_bpm_nonneg"),
        CheckConstraint("energy IS NULL OR (energy >= 0 AND energy <= 1)", name="ck_tracks_energy_range"),
    )

    id = Column(Integer, primary_key=True)
    path = Column(Text, unique=True, nullable=False)
    title = Column(Text)
    artist = Column(Text)
    album = Column(Text)
    albumartist = Column(Text)
    year = Column(Text)
    genre = Column(Text)
    tracknumber = Column(Text)
    discnumber = Column(Text)
    composer = Column(Text)
    bpm = Column(Float)
    key = Column(Text)
    loudness_lufs = Column(Float)
    duration = Column(Integer)
    file_size = Column(Integer)
    file_mtime = Column(Float)
    file_hash = Column(Text)
    format = Column(Text)
    bitrate = Column(Integer)
    sample_rate = Column(Integer)
    play_count = Column(Integer, default=0)
    rating = Column(Integer, default=0)
    energy = Column(Float)
    mood = Column(Text)
    comment = Column(Text)
    lyrics = Column(Text)
    isrc = Column(Text)
    publisher = Column(Text)
    grouping = Column(Text)
    copyright = Column(Text)
    remixer = Column(Text)
    cue_in_ms = Column(Integer)
    cue_out_ms = Column(Integer)
    fingerprint = Column(Text)
    waveform_path = Column(Text)
    artwork_path = Column(Text)
    date_added = Column(DateTime, default=func.now())
    date_modified = Column(DateTime)

    tags = relationship("TagOrm", back_populates="track", cascade="all, delete-orphan")
    cue_points = relationship("CuePointOrm", back_populates="track", cascade="all, delete-orphan")
    beat_markers = relationship("BeatMarkerOrm", back_populates="track", cascade="all, delete-orphan")
    analysis_jobs = relationship("AnalysisJobOrm", back_populates="track", cascade="all, delete-orphan")
    audio_features = relationship("AudioFeaturesOrm", back_populates="track", uselist=False, cascade="all, delete-orphan")


class TagOrm(Base):
    __tablename__ = "tags"
    __table_args__ = (
        Index("ix_tags_track", "track_id"),
        Index("ix_tags_tag", "tag"),
    )

    id = Column(Integer, primary_key=True)
    track_id = Column(Integer, ForeignKey("tracks.id"), nullable=False)
    tag = Column(Text, nullable=False)
    source = Column(Text, default="user")
    confidence = Column(Float)
    created_at = Column(DateTime, default=func.now())

    track = relationship("TrackOrm", back_populates="tags")


class PlaylistOrm(Base):
    __tablename__ = "playlists"

    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=func.now())
    modified_at = Column(DateTime, default=func.now(), onupdate=func.now())
    is_smart = Column(Integer, default=0)
    rules = Column(Text)


class PlaylistTrackOrm(Base):
    __tablename__ = "playlist_tracks"
    __table_args__ = (Index("ix_playlist_tracks_playlist", "playlist_id", "position"),)

    playlist_id = Column(Integer, ForeignKey("playlists.id"), primary_key=True)
    track_id = Column(Integer, ForeignKey("tracks.id"), primary_key=True)
    position = Column(Integer, default=0)


class SettingsOrm(Base):
    __tablename__ = "settings"

    key = Column(Text, primary_key=True)
    value = Column(Text)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class ChangeLogOrm(Base):
    __tablename__ = "change_log"

    id = Column(Integer, primary_key=True)
    track_id = Column(Integer, ForeignKey("tracks.id"), nullable=False)
    field = Column(Text, nullable=False)
    old_value = Column(Text)
    new_value = Column(Text)
    source = Column(Text, default="user")
    changed_at = Column(DateTime, default=func.now())


class MetadataFieldEvidenceOrm(Base):
    __tablename__ = "metadata_field_evidence"
    __table_args__ = (
        Index("ix_metadata_field_evidence_track_field", "track_id", "field_name"),
        Index("ix_metadata_field_evidence_source", "source"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    track_id = Column(Integer, ForeignKey("tracks.id", ondelete="CASCADE"), nullable=False)
    field_name = Column(Text, nullable=False)
    value = Column(Text)
    source = Column(Text, nullable=False)
    confidence = Column(Float, nullable=False, default=0.0)
    verified = Column(Boolean, nullable=False, default=False)
    observed_at = Column(DateTime, default=func.now())
    version = Column(Integer, nullable=False, default=1)


class MetadataConflictOrm(Base):
    __tablename__ = "metadata_conflicts"
    __table_args__ = (
        Index("ix_metadata_conflicts_track_field", "track_id", "field_name"),
        Index("ix_metadata_conflicts_status", "status"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    track_id = Column(Integer, ForeignKey("tracks.id", ondelete="CASCADE"), nullable=False)
    field_name = Column(Text, nullable=False)
    chosen_value = Column(Text)
    chosen_source = Column(Text)
    reason = Column(Text, nullable=False)
    status = Column(Text, nullable=False, default="open")
    variants_json = Column(Text, nullable=False, default="[]")
    detected_at = Column(DateTime, default=func.now())
    resolved_at = Column(DateTime)


class MetadataHistoryOrm(Base):
    __tablename__ = "metadata_history"
    __table_args__ = (Index("ix_metadata_history_track_field", "track_id", "field_name"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    track_id = Column(Integer, ForeignKey("tracks.id", ondelete="CASCADE"), nullable=False)
    field_name = Column(Text, nullable=False)
    old_value = Column(Text)
    new_value = Column(Text)
    source = Column(Text, nullable=False)
    confidence = Column(Float, nullable=False, default=0.0)
    verified = Column(Boolean, nullable=False, default=False)
    version = Column(Integer, nullable=False, default=1)
    operation = Column(Text, nullable=False, default="consensus")
    changed_at = Column(DateTime, default=func.now())


class MetadataCacheOrm(Base):
    __tablename__ = "metadata_cache"
    __table_args__ = (Index("ix_metadata_cache_created", "created_at"),)

    key = Column(Text, primary_key=True)
    payload = Column(Text, nullable=False)
    source = Column(Text)
    created_at = Column(DateTime, default=func.now())


class CuePointOrm(Base):
    __tablename__ = "cue_points"
    __table_args__ = (Index("ix_cue_points_track", "track_id"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    track_id = Column(Integer, ForeignKey("tracks.id", ondelete="CASCADE"), nullable=False)
    time_ms = Column(Integer, nullable=False)
    cue_type = Column(String(20), nullable=False, default="hotcue")
    hotcue_index = Column(Integer, nullable=True)
    loop_end_ms = Column(Integer, nullable=True)
    label = Column(String(100), nullable=True)
    color = Column(String(10), nullable=True)
    created_at = Column(DateTime, default=func.now())

    track = relationship("TrackOrm", back_populates="cue_points")


class BeatMarkerOrm(Base):
    __tablename__ = "beat_markers"
    __table_args__ = (Index("ix_beat_markers_track", "track_id"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    track_id = Column(Integer, ForeignKey("tracks.id", ondelete="CASCADE"), nullable=False)
    time_ms = Column(Float, nullable=False)
    beat_number = Column(Integer, nullable=False)
    bar_number = Column(Integer, nullable=False)
    confidence = Column(Float)
    created_at = Column(DateTime, default=func.now())

    track = relationship("TrackOrm", back_populates="beat_markers")


class AnalysisJobOrm(Base):
    __tablename__ = "analysis_jobs"
    __table_args__ = (Index("ix_analysis_jobs_track", "track_id"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    track_id = Column(Integer, ForeignKey("tracks.id", ondelete="CASCADE"), nullable=False)
    job_type = Column(String(30), nullable=False)
    priority = Column(Integer, nullable=False, default=5)
    status = Column(String(20), nullable=False, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    error_msg = Column(Text, nullable=True)
    finished_at = Column(DateTime)

    track = relationship("TrackOrm", back_populates="analysis_jobs")


class AudioFeaturesOrm(Base):
    __tablename__ = "audio_features"

    id = Column(Integer, ForeignKey("tracks.id", ondelete="CASCADE"), primary_key=True)
    mfcc_json = Column(Text, nullable=False, default="[]")
    tempo = Column(Float, nullable=True)
    spectral_centroid = Column(Float, nullable=True)
    spectral_rolloff = Column(Float, nullable=True)
    brightness = Column(Float, nullable=True)
    roughness = Column(Float, nullable=True)
    zero_crossing_rate = Column(Float)
    chroma_json = Column(Text)
    danceability = Column(Float)
    valence = Column(Float)
    waveform_blob = Column(LargeBinary, nullable=True)
    created_at = Column(DateTime, default=func.now())

    track = relationship("TrackOrm", back_populates="audio_features")


class WatchFolderOrm(Base):
    __tablename__ = "watch_folders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    path = Column(String(1024), nullable=False, unique=True)
    active = Column(Boolean, nullable=False, default=True)
