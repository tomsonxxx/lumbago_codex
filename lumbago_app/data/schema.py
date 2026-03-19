from __future__ import annotations

from sqlalchemy import CheckConstraint, Column, DateTime, Float, ForeignKey, Index, Integer, String, Text, func
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
    year = Column(Text)
    genre = Column(Text)
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
    cue_in_ms = Column(Integer)
    cue_out_ms = Column(Integer)
    fingerprint = Column(Text)
    waveform_path = Column(Text)
    artwork_path = Column(Text)
    date_added = Column(DateTime, default=func.now())
    date_modified = Column(DateTime)

    tags = relationship("TagOrm", back_populates="track", cascade="all, delete-orphan")


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

    id = Column(Integer, primary_key=True)
    track_id = Column(Integer, ForeignKey("tracks.id"), nullable=False)
    time_ms = Column(Integer, nullable=False)
    cue_type = Column(Text, default="hotcue")
    hotcue_index = Column(Integer)
    loop_end_ms = Column(Integer)
    label = Column(Text)
    color = Column(Text)
    created_at = Column(DateTime, default=func.now())

    track = relationship("TrackOrm")


class BeatMarkerOrm(Base):
    __tablename__ = "beat_markers"
    __table_args__ = (Index("ix_beat_markers_track", "track_id"),)

    id = Column(Integer, primary_key=True)
    track_id = Column(Integer, ForeignKey("tracks.id"), nullable=False)
    time_ms = Column(Integer, nullable=False)
    beat_number = Column(Integer)
    confidence = Column(Float)
    created_at = Column(DateTime, default=func.now())

    track = relationship("TrackOrm")


class AnalysisJobOrm(Base):
    __tablename__ = "analysis_jobs"
    __table_args__ = (Index("ix_analysis_jobs_track", "track_id"),)

    id = Column(Integer, primary_key=True)
    track_id = Column(Integer, ForeignKey("tracks.id"), nullable=False)
    job_type = Column(Text, nullable=False)
    status = Column(Text, default="pending")
    error_message = Column(Text)
    created_at = Column(DateTime, default=func.now())
    finished_at = Column(DateTime)

    track = relationship("TrackOrm")


class AudioFeaturesOrm(Base):
    __tablename__ = "audio_features"
    __table_args__ = (Index("ix_audio_features_track", "track_id"),)

    id = Column(Integer, primary_key=True)
    track_id = Column(Integer, ForeignKey("tracks.id"), nullable=False, unique=True)
    spectral_centroid = Column(Float)
    spectral_rolloff = Column(Float)
    zero_crossing_rate = Column(Float)
    mfcc_json = Column(Text)
    chroma_json = Column(Text)
    tempo = Column(Float)
    danceability = Column(Float)
    valence = Column(Float)
    created_at = Column(DateTime, default=func.now())

    track = relationship("TrackOrm")
