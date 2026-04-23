from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import Iterable

from mutagen import File as MutagenFile
import re
from mutagen.id3 import ID3, ID3NoHeaderError
from mutagen.mp4 import MP4FreeForm

from lumbago_app.core.models import Track
from lumbago_app.core.config import load_settings


AUDIO_EXTENSIONS = {".mp3", ".flac", ".m4a", ".mp4", ".wav", ".ogg", ".aac", ".aiff"}
_MP4_EXTENSIONS = {".m4a", ".mp4"}
_MP4_FREEFORM_PREFIX = "----:com.apple.iTunes:"


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
    audio = _open_mutagen(path)
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
    track.albumartist = tag_value("TPE2") or tag_value("albumartist") or tag_value("album artist")
    track.year = (
        tag_value("TDRC")
        or tag_value("date")
        or tag_value("year")
        or tag_value("TYER")
    )
    track.genre = tag_value("TCON") or tag_value("genre")
    track.tracknumber = tag_value("TRCK") or tag_value("tracknumber")
    track.discnumber = tag_value("TPOS") or tag_value("discnumber")
    track.composer = tag_value("TCOM") or tag_value("composer")
    track.bpm = _parse_float_tag(
        tag_value("TBPM")
        or tag_value("bpm")
        or tag_value("BPM")
        or tag_value("tempo")
    )
    track.key = (
        tag_value("TKEY")
        or tag_value("initialkey")
        or tag_value("key")
        or tag_value("INITIALKEY")
    )
    track.rating = _parse_rating_tag(
        tag_value("POPM")
        or tag_value("rating")
        or tag_value("RATING")
    ) or 0
    track.mood = tag_value("mood") or tag_value("MOOD")
    track.energy = _parse_float_tag(tag_value("energy") or tag_value("ENERGY"))
    track.comment = tag_value("COMM") or tag_value("comment") or tag_value("COMM::eng")
    track.lyrics = tag_value("USLT") or tag_value("lyrics") or tag_value("USLT::eng")
    track.isrc = tag_value("TSRC") or tag_value("isrc")
    track.publisher = tag_value("TPUB") or tag_value("organization") or tag_value("label")
    track.grouping = tag_value("TIT1") or tag_value("grouping") or tag_value("contentgroup")
    track.copyright = tag_value("TCOP") or tag_value("copyright")
    track.remixer = tag_value("TPE4") or tag_value("remixer")
    # MP4/M4A uses a different tagging scheme; normalize through read_tags to fill gaps.
    canonical_tags = read_tags(path)
    if canonical_tags:
        _fill_if_empty(track, "title", canonical_tags.get("title"))
        _fill_if_empty(track, "artist", canonical_tags.get("artist"))
        _fill_if_empty(track, "album", canonical_tags.get("album"))
        _fill_if_empty(track, "albumartist", canonical_tags.get("albumartist"))
        _fill_if_empty(track, "year", canonical_tags.get("year"))
        _fill_if_empty(track, "genre", canonical_tags.get("genre"))
        _fill_if_empty(track, "tracknumber", canonical_tags.get("tracknumber"))
        _fill_if_empty(track, "discnumber", canonical_tags.get("discnumber"))
        _fill_if_empty(track, "composer", canonical_tags.get("composer"))
        if track.bpm is None:
            track.bpm = _parse_float_tag(canonical_tags.get("bpm"))
        _fill_if_empty(track, "key", canonical_tags.get("key"))
        if not track.rating:
            track.rating = _parse_rating_tag(canonical_tags.get("rating")) or 0
        _fill_if_empty(track, "mood", canonical_tags.get("mood"))
        if track.energy is None:
            track.energy = _parse_float_tag(canonical_tags.get("energy"))
        _fill_if_empty(track, "comment", canonical_tags.get("comment"))
        _fill_if_empty(track, "lyrics", canonical_tags.get("lyrics"))
        _fill_if_empty(track, "isrc", canonical_tags.get("isrc"))
        _fill_if_empty(track, "publisher", canonical_tags.get("publisher"))
        _fill_if_empty(track, "grouping", canonical_tags.get("grouping"))
        _fill_if_empty(track, "copyright", canonical_tags.get("copyright"))
        _fill_if_empty(track, "remixer", canonical_tags.get("remixer"))
    apply_local_metadata(track, path)
    return track


def read_tags(path: Path) -> dict[str, str]:
    if path.suffix.lower() in _MP4_EXTENSIONS:
        return _read_mp4_tags(path)

    audio = _open_mutagen(path, easy=True)
    if audio is None or audio.tags is None:
        return {}
    _normalize_map = {
        "date": "year", "year": "year",
        "initialkey": "key",
        "albumartist": "albumartist", "album artist": "albumartist",
        "tracknumber": "tracknumber",
        "discnumber": "discnumber",
        "composer": "composer",
        "rating": "rating", "popm": "rating",
        "comment": "comment",
        "lyrics": "lyrics",
        "isrc": "isrc",
        "organization": "publisher", "label": "publisher",
        "grouping": "grouping", "contentgroup": "grouping",
        "copyright": "copyright",
        "remixer": "remixer",
    }
    tags = {}
    for key, value in audio.tags.items():
        normalized = _normalize_map.get(key, key)
        if isinstance(value, list):
            tags[normalized] = ", ".join(str(v) for v in value)
        else:
            tags[normalized] = str(value)
    return tags


def write_tags(path: Path, tags: dict[str, str]) -> None:
    if path.suffix.lower() in _MP4_EXTENSIONS:
        _write_mp4_tags(path, tags)
        return

    audio = _open_mutagen(path, easy=True)
    if audio is None:
        return
    if audio.tags is None:
        try:
            ID3(path).save()
        except ID3NoHeaderError:
            ID3().save(path)
        audio = _open_mutagen(path, easy=True)
    key_map = {
        "key": "initialkey", "year": "date",
        "albumartist": "albumartist", "publisher": "organization",
        "grouping": "contentgroup",
    }
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
    audio = _open_mutagen(path, easy=True)
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
    cleaned = _cleanup_filename_tokens(path.stem)
    parts = [p.strip() for p in cleaned.split(" - ") if p.strip()]
    if len(parts) >= 2:
        possible_title = parts[-1]
        possible_artist = parts[-2] if len(parts) >= 2 else None
        _fill_if_empty(track, "title", possible_title)
        _fill_if_empty(track, "artist", possible_artist)
    elif len(parts) == 1:
        _fill_if_empty(track, "title", parts[0])


_FILENAME_NOISE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(
        r"[\[(]\s*(official(\s+music)?\s+video|official\s+audio|lyrics?|lyric\s+video|visualizer|"
        r"hq|hd|4k|8k|remaster(ed)?|live|explicit)\s*[\])]",
        re.IGNORECASE,
    ),
    re.compile(r"\b(official(\s+music)?\s+video|official\s+audio|lyrics?|lyric\s+video|visualizer)\b", re.IGNORECASE),
)


def _cleanup_filename_tokens(value: str) -> str:
    text = value.replace("_", " ").replace(".", " ")
    for pattern in _FILENAME_NOISE_PATTERNS:
        text = pattern.sub(" ", text)
    text = re.sub(r"[^\w\s\-]", " ", text, flags=re.UNICODE)
    text = re.sub(r"\s+", " ", text).strip(" -_")
    return text


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


def _parse_float_tag(value: str | None) -> float | None:
    if value is None:
        return None
    try:
        return float(str(value).replace(",", "."))
    except ValueError:
        return None


def _parse_rating_tag(value: str | None) -> int | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    match = re.search(r"\d+", text)
    if not match:
        return None
    rating = int(match.group(0))
    # ID3 POPM commonly uses 0..255 scale.
    if rating > 5:
        rating = max(0, min(5, round((rating / 255) * 5)))
    return rating if 0 <= rating <= 5 else None


def file_hash(path: Path) -> str:
    hasher = hashlib.md5()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _read_mp4_tags(path: Path) -> dict[str, str]:
    audio = _open_mutagen(path)
    if audio is None or audio.tags is None:
        return {}
    tags = audio.tags
    out: dict[str, str] = {}

    standard_map = {
        "title": "\xa9nam",
        "artist": "\xa9ART",
        "album": "\xa9alb",
        "albumartist": "aART",
        "year": "\xa9day",
        "genre": "\xa9gen",
        "composer": "\xa9wrt",
        "comment": "\xa9cmt",
        "lyrics": "\xa9lyr",
        "grouping": "\xa9grp",
        "copyright": "cprt",
    }
    for field_name, atom in standard_map.items():
        value = _mp4_first_text(tags.get(atom))
        if value is not None:
            out[field_name] = value

    tracknumber = _mp4_index_value(tags.get("trkn"))
    if tracknumber is not None:
        out["tracknumber"] = tracknumber
    discnumber = _mp4_index_value(tags.get("disk"))
    if discnumber is not None:
        out["discnumber"] = discnumber

    bpm = _mp4_first_text(tags.get("tmpo"))
    if bpm is not None:
        out["bpm"] = bpm

    for field_name, freeform_key in {
        "key": "INITIALKEY",
        "mood": "MOOD",
        "energy": "ENERGY",
        "isrc": "ISRC",
        "publisher": "PUBLISHER",
        "remixer": "REMIXER",
        "rating": "RATING",
    }.items():
        value = _mp4_first_text(tags.get(f"{_MP4_FREEFORM_PREFIX}{freeform_key}"))
        if value is not None:
            out[field_name] = value

    return out


def _write_mp4_tags(path: Path, tags: dict[str, str]) -> None:
    audio = _open_mutagen(path)
    if audio is None:
        return
    if audio.tags is None:
        return

    standard_map = {
        "title": "\xa9nam",
        "artist": "\xa9ART",
        "album": "\xa9alb",
        "albumartist": "aART",
        "year": "\xa9day",
        "genre": "\xa9gen",
        "composer": "\xa9wrt",
        "comment": "\xa9cmt",
        "lyrics": "\xa9lyr",
        "grouping": "\xa9grp",
        "copyright": "cprt",
    }
    for field_name, atom in standard_map.items():
        if field_name not in tags:
            continue
        value = tags.get(field_name)
        if value is None or value == "":
            if atom in audio.tags:
                del audio.tags[atom]
            continue
        audio.tags[atom] = [str(value)]

    for field_name, atom in {"tracknumber": "trkn", "discnumber": "disk"}.items():
        if field_name not in tags:
            continue
        value = tags.get(field_name)
        if value is None or value == "":
            if atom in audio.tags:
                del audio.tags[atom]
            continue
        parsed = _parse_index_tag(value)
        if parsed is not None:
            audio.tags[atom] = [(parsed, 0)]

    if "bpm" in tags:
        bpm_value = tags.get("bpm")
        if bpm_value is None or bpm_value == "":
            if "tmpo" in audio.tags:
                del audio.tags["tmpo"]
        else:
            try:
                audio.tags["tmpo"] = [int(round(float(str(bpm_value).replace(",", "."))))]
            except (TypeError, ValueError):
                pass

    for field_name, freeform_key in {
        "key": "INITIALKEY",
        "mood": "MOOD",
        "energy": "ENERGY",
        "isrc": "ISRC",
        "publisher": "PUBLISHER",
        "remixer": "REMIXER",
        "rating": "RATING",
    }.items():
        if field_name not in tags:
            continue
        atom = f"{_MP4_FREEFORM_PREFIX}{freeform_key}"
        value = tags.get(field_name)
        if value is None or value == "":
            if atom in audio.tags:
                del audio.tags[atom]
            continue
        audio.tags[atom] = [_mp4_encode_text(str(value))]

    audio.save()


def _mp4_encode_text(value: str) -> MP4FreeForm:
    return MP4FreeForm(value.encode("utf-8"), dataformat=1)


def _mp4_first_text(value) -> str | None:
    if value is None:
        return None
    if isinstance(value, list):
        if not value:
            return None
        value = value[0]
    if isinstance(value, tuple):
        if not value:
            return None
        value = value[0]
    if isinstance(value, bytes):
        try:
            return value.decode("utf-8", errors="ignore").strip() or None
        except Exception:
            return None
    text = str(value).strip()
    return text or None


def _mp4_index_value(value) -> str | None:
    if value is None:
        return None
    if isinstance(value, list) and value:
        first = value[0]
        if isinstance(first, tuple) and first:
            return str(first[0])
    return _mp4_first_text(value)


def _parse_index_tag(value) -> int | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    match = re.search(r"\d+", text)
    if not match:
        return None
    try:
        return int(match.group(0))
    except ValueError:
        return None


def _open_mutagen(path: Path, easy: bool = False):
    if easy:
        try:
            return MutagenFile(path, easy=True)
        except TypeError:
            # Test stubs may not accept keyword arguments.
            return MutagenFile(path)
    return MutagenFile(path)
