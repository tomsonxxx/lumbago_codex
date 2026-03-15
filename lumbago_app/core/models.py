from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class CuePoint:
    time_ms: int
    cue_type: str
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


@dataclass
class Track:
    path: str
    title: str | None = None
    artist: str | None = None
    album: str | None = None
    year: str | None = None
    genre: str | None = None
    bpm: float | None = None
    key: str | None = None
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
