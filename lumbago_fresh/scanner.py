from __future__ import annotations

from pathlib import Path
from typing import Iterable

from .models import Track

try:
    from mutagen import File as MutagenFile
except Exception:  # pragma: no cover
    MutagenFile = None


AUDIO_EXTENSIONS = {
    ".mp3",
    ".flac",
    ".wav",
    ".m4a",
    ".aac",
    ".ogg",
    ".wma",
}


def iter_audio_files(root: Path) -> Iterable[Path]:
    if not root.exists():
        return
    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() in AUDIO_EXTENSIONS:
            yield path


def _pick_tag(tags: dict, keys: tuple[str, ...]) -> str:
    for key in keys:
        value = tags.get(key)
        if value is None:
            continue
        if isinstance(value, list) and value:
            return str(value[0]).strip()
        text = str(value).strip()
        if text:
            return text
    return ""


def extract_track(path: Path, source: str = "import") -> Track:
    track = Track(path=str(path), source=source)
    if MutagenFile is None:
        _apply_title_fallback(track)
        return track

    try:
        audio = MutagenFile(path)
    except Exception:
        audio = None

    if audio is None:
        _apply_title_fallback(track)
        return track

    tags = audio.tags or {}
    track.title = _pick_tag(tags, ("TIT2", "title", "\xa9nam")) or path.stem
    track.artist = _pick_tag(tags, ("TPE1", "artist", "\xa9ART"))
    track.album = _pick_tag(tags, ("TALB", "album", "\xa9alb"))
    track.genre = _pick_tag(tags, ("TCON", "genre", "\xa9gen"))
    track.year = _pick_tag(tags, ("TDRC", "date", "\xa9day"))[:4]
    try:
        track.duration = float(getattr(audio.info, "length", 0.0) or 0.0)
    except Exception:
        track.duration = 0.0
    return track


def _apply_title_fallback(track: Track) -> None:
    if not track.title:
        track.title = Path(track.path).stem


def auto_tag_from_filename(track: Track) -> Track:
    """
    Lokalna automatyzacja w stylu "AI tagger":
    próbuje wyciągnąć artystę i tytuł z nazwy pliku "Artist - Title".
    """
    if track.analyzed:
        return track
    stem = Path(track.path).stem
    if " - " in stem:
        artist, title = stem.split(" - ", 1)
        if not track.artist:
            track.artist = artist.strip()
        if not track.title or track.title == stem:
            track.title = title.strip()
    elif not track.title:
        track.title = stem
    track.analyzed = True
    return track

