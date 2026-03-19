from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import Iterable

from mutagen import File as MutagenFile
import re
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, ID3NoHeaderError

from lumbago_app.core.models import Track
from lumbago_app.core.config import load_settings


AUDIO_EXTENSIONS = {".mp3", ".flac", ".m4a", ".mp4", ".wav", ".ogg", ".aac", ".aiff"}


def iter_audio_files(
    folder: Path, recursive: bool = True, extensions: set[str] | None = None
) -> Iterable[Path]:
    exts = {e.lower() for e in (extensions or AUDIO_EXTENSIONS)}
    if recursive:
        for root, _, files in os.walk(folder):
            for name in files:
                path = Path(root) / name
                if path.suffix.lower() in exts:
                    yield path
    else:
        for path in folder.iterdir():
            if path.is_file() and path.suffix.lower() in exts:
                yield path


def extract_metadata(path: Path) -> Track:
    audio = MutagenFile(path)
    size = path.stat().st_size
    mtime = path.stat().st_mtime
    track = Track(path=str(path), file_size=size, file_mtime=mtime)
    if audio is None:
        return track

    track.format = audio.mime[0] if hasattr(audio, "mime") and audio.mime else None
    if hasattr(audio, "info") and audio.info:
        track.duration = int(getattr(audio.info, "length", 0) or 0)
        track.bitrate = int(getattr(audio.info, "bitrate", 0) or 0) // 1000 or None
        track.sample_rate = int(getattr(audio.info, "sample_rate", 0) or 0) or None

    tags = audio.tags or {}
    def tag_value(key: str) -> str | None:
        value = tags.get(key)
        if value is None:
            return None
        if hasattr(value, "text"):
            return ", ".join(str(v) for v in value.text)
        if isinstance(value, list):
            return ", ".join(str(v) for v in value)
        return str(value)

    track.title = tag_value("TIT2") or tag_value("title")
    track.artist = tag_value("TPE1") or tag_value("artist")
    track.album = tag_value("TALB") or tag_value("album")
    track.year = (
        tag_value("TDRC")
        or tag_value("date")
        or tag_value("year")
        or tag_value("TYER")
    )
    track.genre = tag_value("TCON") or tag_value("genre")
    apply_local_metadata(track, path)
    return track


def read_tags(path: Path) -> dict[str, str]:
    audio = MutagenFile(path, easy=True)
    if audio is None or audio.tags is None:
        return {}
    tags = {}
    for key, value in audio.tags.items():
        if key in {"date", "year"}:
            key = "year"
        if key == "initialkey":
            key = "key"
        if isinstance(value, list):
            tags[key] = ", ".join(str(v) for v in value)
        else:
            tags[key] = str(value)
    return tags


def write_tags(path: Path, tags: dict[str, str]) -> None:
    audio = MutagenFile(path, easy=True)
    if audio is None:
        return
    if audio.tags is None:
        try:
            ID3(path).save()
        except ID3NoHeaderError:
            ID3().save(path)
        audio = MutagenFile(path, easy=True)
    key_map = {"key": "initialkey", "year": "date"}
    for key, value in tags.items():
        target_key = key_map.get(key, key)
        if value is None or value == "":
            if target_key in audio:
                del audio[target_key]
            continue
        try:
            audio[target_key] = [value]
        except Exception:
            continue
    audio.save()


def clear_tags(path: Path) -> None:
    audio = MutagenFile(path, easy=True)
    if audio is None or audio.tags is None:
        return
    audio.tags.clear()
    audio.save()


def apply_local_metadata(track: Track, path: Path) -> None:
    _apply_folder_json(track, path)
    _apply_sidecar_json(track, path)
    _apply_filename_metadata(track, path)
    _apply_filename_patterns(track, path)
    _apply_cue_metadata(track, path)
    _apply_folder_metadata(track, path)


def _apply_sidecar_json(track: Track, path: Path) -> None:
    sidecar = path.with_suffix(".json")
    if not sidecar.exists():
        return
    try:
        import json

        payload = json.loads(sidecar.read_text(encoding="utf-8"))
    except Exception:
        return
    _fill_if_empty(track, "title", payload.get("title"))
    _fill_if_empty(track, "artist", payload.get("artist"))
    _fill_if_empty(track, "album", payload.get("album"))
    _fill_if_empty(track, "genre", payload.get("genre"))
    _fill_if_empty(track, "key", payload.get("key"))
    _fill_if_empty(track, "mood", payload.get("mood"))
    _fill_if_empty(track, "energy", payload.get("energy"))
    _fill_if_empty(track, "bpm", payload.get("bpm"))


def _apply_folder_json(track: Track, path: Path) -> None:
    for name in ("folder.json", "metadata.json"):
        file_path = path.parent / name
        if not file_path.exists():
            continue
        try:
            import json

            payload = json.loads(file_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        _fill_if_empty(track, "album", payload.get("album"))
        _fill_if_empty(track, "artist", payload.get("artist"))
        _fill_if_empty(track, "genre", payload.get("genre"))
        _fill_if_empty(track, "key", payload.get("key"))
        _fill_if_empty(track, "mood", payload.get("mood"))
        _fill_if_empty(track, "energy", payload.get("energy"))
        _fill_if_empty(track, "bpm", payload.get("bpm"))
        break


def _apply_filename_metadata(track: Track, path: Path) -> None:
    name = path.stem
    cleaned = name.replace("_", " ").replace(".", " ").strip()
    parts = [p.strip() for p in cleaned.split(" - ") if p.strip()]
    if len(parts) >= 2:
        possible_title = parts[-1]
        possible_artist = parts[-2] if len(parts) >= 2 else None
        _fill_if_empty(track, "title", possible_title)
        _fill_if_empty(track, "artist", possible_artist)
    elif len(parts) == 1:
        _fill_if_empty(track, "title", parts[0])


def _apply_filename_patterns(track: Track, path: Path) -> None:
    settings = load_settings()
    patterns = settings.filename_patterns or []
    if not patterns:
        return
    name = path.stem
    for pattern in patterns:
        try:
            match = re.match(pattern, name)
        except re.error:
            continue
        if not match:
            continue
        groups = match.groupdict()
        _fill_if_empty(track, "artist", groups.get("artist"))
        _fill_if_empty(track, "title", groups.get("title"))
        _fill_if_empty(track, "album", groups.get("album"))
        _fill_if_empty(track, "genre", groups.get("genre"))
        _fill_if_empty(track, "key", groups.get("key"))
        _fill_if_empty(track, "bpm", groups.get("bpm"))
        break


def _apply_cue_metadata(track: Track, path: Path) -> None:
    cue_path = path.with_suffix(".cue")
    if not cue_path.exists():
        cue_path = path.parent / "album.cue"
    if not cue_path.exists():
        return
    try:
        lines = cue_path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except Exception:
        return
    album_title = None
    album_artist = None
    current_file = None
    in_track = False
    track_title = None
    track_artist = None
    for line in lines:
        stripped = line.strip()
        if stripped.upper().startswith("TITLE") and not in_track:
            album_title = _parse_cue_value(stripped)
        elif stripped.upper().startswith("PERFORMER") and not in_track:
            album_artist = _parse_cue_value(stripped)
        elif stripped.upper().startswith("FILE"):
            current_file = _parse_cue_file(stripped)
            in_track = False
        elif stripped.upper().startswith("TRACK"):
            in_track = True
            track_title = None
            track_artist = None
        elif stripped.upper().startswith("TITLE") and in_track:
            track_title = _parse_cue_value(stripped)
        elif stripped.upper().startswith("PERFORMER") and in_track:
            track_artist = _parse_cue_value(stripped)

        if current_file and Path(current_file).name == path.name and in_track and track_title:
            _fill_if_empty(track, "title", track_title)
            _fill_if_empty(track, "artist", track_artist or album_artist)
            _fill_if_empty(track, "album", album_title)
            break


def _parse_cue_value(line: str) -> str | None:
    parts = line.split(" ", 1)
    if len(parts) < 2:
        return None
    value = parts[1].strip().strip('"')
    return value or None


def _parse_cue_file(line: str) -> str | None:
    parts = line.split(" ", 2)
    if len(parts) < 2:
        return None
    value = parts[1].strip().strip('"')
    return value or None


def _apply_folder_metadata(track: Track, path: Path) -> None:
    parent = path.parent
    album = parent.name if parent else None
    artist = parent.parent.name if parent and parent.parent else None
    if album and " - " in album:
        parts = [p.strip() for p in album.split(" - ") if p.strip()]
        if len(parts) >= 2:
            artist = artist or parts[0]
            album = album or parts[1]
    _fill_if_empty(track, "album", album)
    _fill_if_empty(track, "artist", artist)


def _fill_if_empty(track: Track, field: str, value) -> None:
    if value is None:
        return
    if hasattr(track, field):
        current = getattr(track, field)
        if current:
            return
        setattr(track, field, value)


def file_hash(path: Path) -> str:
    hasher = hashlib.md5()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()
