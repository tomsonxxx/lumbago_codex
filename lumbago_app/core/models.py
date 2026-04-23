from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class CuePoint:
    time_ms: int
    cue_type: str = "hotcue"
    hotcue_index: int | None = None
    loop_end_ms: int | None = None
    label: str | None = None
    color: str | None = None


@dataclass
class Tag:
    value: str
    source: str = "user"
    confidence: float | None = None


@dataclass
class AnalysisResult:
    bpm: float | None = None
    key: str | None = None
    mood: str | None = None
    energy: float | None = None
    genre: str | None = None
    description: str | None = None
    confidence: float | None = None
    title: str | None = None
    artist: str | None = None
    album: str | None = None
    albumartist: str | None = None
    year: str | None = None
    tracknumber: str | None = None
    discnumber: str | None = None
    composer: str | None = None
    isrc: str | None = None
    publisher: str | None = None
    lyrics: str | None = None
    grouping: str | None = None
    copyright: str | None = None
    remixer: str | None = None
    comment: str | None = None


@dataclass
class Track:
    path: str
    title: str | None = None
    artist: str | None = None
    album: str | None = None
    albumartist: str | None = None
    year: str | None = None
    genre: str | None = None
    tracknumber: str | None = None
    discnumber: str | None = None
    composer: str | None = None
    bpm: float | None = None
    key: str | None = None
    loudness_lufs: float | None = None
    duration: int | None = None
    file_size: int | None = None
    file_mtime: float | None = None
    file_hash: str | None = None
    format: str | None = None
    bitrate: int | None = None
    sample_rate: int | None = None
    play_count: int = 0
    rating: int = 0
    energy: float | None = None
    mood: str | None = None
    comment: str | None = None
    lyrics: str | None = None
    isrc: str | None = None
    publisher: str | None = None
    grouping: str | None = None
    copyright: str | None = None
    remixer: str | None = None
    cue_in_ms: int | None = None
    cue_out_ms: int | None = None
    fingerprint: str | None = None
    waveform_path: str | None = None
    artwork_path: str | None = None
    date_added: datetime | None = None
    date_modified: datetime | None = None
    tags: list[Tag] = field(default_factory=list)


@dataclass
class Playlist:
    name: str
    description: str | None = None
    is_smart: bool = False
    rules: str | None = None
    playlist_id: int | None = None


@dataclass
class DuplicateGroup:
    track_ids: list[int]
    similarity: float


@dataclass
class ImportJob:
    total_files: int
    processed_files: int = 0
    errors: int = 0


@dataclass
class BeatMarker:
    time_ms: float
    beat_number: int
    bar_number: int
    confidence: float | None = None


@dataclass
class AnalysisJob:
    track_id: int
    job_type: str
    priority: int = 5
    status: str = "pending"
    created_at: datetime | None = None
    updated_at: datetime | None = None
    error_msg: str | None = None
    job_id: int | None = None


@dataclass
class AudioFeatures:
    track_id: int
    mfcc_json: str = "[]"
    tempo: float | None = None
    spectral_centroid: float | None = None
    spectral_rolloff: float | None = None
    brightness: float | None = None
    roughness: float | None = None
    zero_crossing_rate: float | None = None
    chroma_json: str | None = None
    danceability: float | None = None
    valence: float | None = None
    waveform_blob: bytes | None = None


@dataclass
class WatchFolder:
    path: str
    active: bool = True
    folder_id: int | None = None
