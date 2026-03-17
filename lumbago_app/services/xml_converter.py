from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from xml.etree import ElementTree as ET


@dataclass
class XmlTrack:
    path: str
    title: str | None = None
    artist: str | None = None
    album: str | None = None
    genre: str | None = None
    bpm: str | None = None
    key: str | None = None
    # lista (num 0-7, pozycja w sekundach)
    hot_cues: list[tuple[int, float]] | None = None


def parse_rekordbox_xml(path: Path) -> list[XmlTrack]:
    tree = ET.parse(path)
    root = tree.getroot()
    collection = root.find("COLLECTION")
    if collection is None:
        return []
    tracks: list[XmlTrack] = []
    for track_node in collection.findall("TRACK"):
        location = track_node.get("Location") or track_node.get("LocationFile") or ""
        if location.startswith("file://"):
            location = location.replace("file://", "")
        hot_cues: list[tuple[int, float]] = []
        for pm in track_node.findall("POSITION_MARK"):
            if pm.get("Type") == "0":  # Type 0 = hot cue w Rekordbox
                try:
                    num = int(pm.get("Num", "0"))
                    pos = float(pm.get("Start", "0"))
                    hot_cues.append((num, pos))
                except (ValueError, TypeError):
                    pass
        tracks.append(
            XmlTrack(
                path=location,
                title=track_node.get("Name"),
                artist=track_node.get("Artist"),
                album=track_node.get("Album"),
                genre=track_node.get("Genre"),
                bpm=track_node.get("BPM"),
                key=track_node.get("Key"),
                hot_cues=hot_cues or None,
            )
        )
    return tracks


def export_virtualdj_xml(tracks: Iterable[XmlTrack], output_path: Path) -> None:
    root = ET.Element("VirtualDJ_Database", Version="8.5")
    for item in tracks:
        song = ET.SubElement(root, "Song")
        song.set("FilePath", item.path or "")
        if item.title:
            song.set("Title", item.title)
        if item.artist:
            song.set("Artist", item.artist)
        if item.album:
            song.set("Album", item.album)
        if item.genre:
            song.set("Genre", item.genre)
        if item.bpm:
            song.set("BPM", item.bpm)
        if item.key:
            song.set("Key", item.key)
        if item.hot_cues:
            for num, pos in item.hot_cues:
                poi = ET.SubElement(song, "Poi")
                poi.set("Pos", f"{pos:.3f}")
                poi.set("Name", f"Cue {num + 1}")
                poi.set("Type", "cue")
                poi.set("Num", str(num))
    tree = ET.ElementTree(root)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tree.write(output_path, encoding="utf-8", xml_declaration=True)


def export_rekordbox_xml(tracks: Iterable[XmlTrack], output_path: Path) -> None:
    """Eksport do formatu Rekordbox XML z hot cues (POSITION_MARK)."""
    root = ET.Element("DJ_PLAYLISTS", Version="1.0.0")
    product = ET.SubElement(root, "PRODUCT")
    product.set("Name", "Lumbago Music AI")
    product.set("Version", "1.0")
    collection = ET.SubElement(root, "COLLECTION")
    track_list = list(tracks)
    collection.set("Entries", str(len(track_list)))
    for idx, item in enumerate(track_list, 1):
        t = ET.SubElement(collection, "TRACK")
        t.set("TrackID", str(idx))
        t.set("Name", item.title or "")
        t.set("Artist", item.artist or "")
        t.set("Album", item.album or "")
        t.set("Genre", item.genre or "")
        t.set("BPM", item.bpm or "")
        t.set("Key", item.key or "")
        loc = item.path.replace("\\", "/")
        if not loc.startswith("file://"):
            loc = "file://" + loc
        t.set("Location", loc)
        if item.hot_cues:
            for num, pos in item.hot_cues:
                pm = ET.SubElement(t, "POSITION_MARK")
                pm.set("Name", f"Cue {num + 1}")
                pm.set("Type", "0")
                pm.set("Start", f"{pos:.3f}")
                pm.set("Num", str(num))
    tree = ET.ElementTree(root)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tree.write(output_path, encoding="utf-8", xml_declaration=True)


def parse_traktor_nml(path: Path) -> list[XmlTrack]:
    """Parsuje kolekcję Traktor NML (.nml)."""
    tree = ET.parse(path)
    root = tree.getroot()
    tracks: list[XmlTrack] = []
    for entry in root.findall(".//ENTRY"):
        loc = entry.find("LOCATION")
        if loc is None:
            continue
        vol = loc.get("VOLUME", "")
        dir_ = loc.get("DIR", "")
        file_ = loc.get("FILE", "")
        # Traktor DIR format: "/:folder/:subfolder/:" → "folder/subfolder/"
        dir_clean = dir_.replace("/:", "/").lstrip("/")
        if vol and vol.endswith(":"):
            # Windows ścieżka: "C:" + "Music\\" + "file.mp3"
            path_str = vol + "\\" + dir_clean.replace("/", "\\") + file_
        else:
            path_str = dir_clean + file_

        tempo = entry.find("TEMPO")
        bpm = tempo.get("BPM") if tempo is not None else None

        info = entry.find("INFO")
        genre = info.get("GENRE") if info is not None else None
        key = info.get("KEY") if info is not None else None
        if not key:
            mk = entry.find("MUSICAL_KEY")
            if mk is not None:
                key = _traktor_key_to_camelot(mk.get("VALUE"))

        album_el = entry.find("ALBUM")
        album = album_el.get("TITLE") if album_el is not None else None

        hot_cues: list[tuple[int, float]] = []
        for cue in entry.findall("CUE_V2"):
            if cue.get("TYPE") == "0":
                try:
                    hc_num = int(cue.get("HOTCUE", "-1"))
                    if hc_num >= 0:
                        pos = float(cue.get("START", "0"))
                        hot_cues.append((hc_num, pos))
                except (ValueError, TypeError):
                    pass

        tracks.append(
            XmlTrack(
                path=path_str,
                title=entry.get("TITLE"),
                artist=entry.get("ARTIST"),
                album=album,
                genre=genre,
                bpm=bpm,
                key=key,
                hot_cues=hot_cues or None,
            )
        )
    return tracks


def export_traktor_nml(tracks: Iterable[XmlTrack], output_path: Path) -> None:
    """Eksport kolekcji do formatu Traktor NML."""
    root = ET.Element("NML", VERSION="19")
    head = ET.SubElement(root, "HEAD")
    head.set("COMPANY", "Native Instruments")
    head.set("PROGRAM", "Traktor")
    ET.SubElement(root, "MUSICFOLDERS")
    track_list = list(tracks)
    collection = ET.SubElement(root, "COLLECTION")
    collection.set("ENTRIES", str(len(track_list)))
    for item in track_list:
        entry = ET.SubElement(collection, "ENTRY")
        entry.set("TITLE", item.title or "")
        entry.set("ARTIST", item.artist or "")
        # LOCATION
        p = Path(item.path) if item.path else Path("")
        loc = ET.SubElement(entry, "LOCATION")
        loc.set("VOLUME", p.drive or "")
        parts = p.parts[1:] if p.drive else p.parts
        dir_path = "/:" + "/:" .join(parts[:-1]) + "/:" if len(parts) > 1 else "/:"
        loc.set("DIR", dir_path)
        loc.set("FILE", p.name)
        # INFO
        info_el = ET.SubElement(entry, "INFO")
        if item.genre:
            info_el.set("GENRE", item.genre)
        if item.key:
            info_el.set("KEY", item.key)
        if item.album:
            album_el = ET.SubElement(entry, "ALBUM")
            album_el.set("TITLE", item.album)
        # TEMPO
        if item.bpm:
            tempo_el = ET.SubElement(entry, "TEMPO")
            tempo_el.set("BPM", str(item.bpm))
        # Hot cues
        if item.hot_cues:
            for num, pos in item.hot_cues:
                cue = ET.SubElement(entry, "CUE_V2")
                cue.set("NAME", f"Cue {num + 1}")
                cue.set("DISPL_ORDER", str(num))
                cue.set("TYPE", "0")
                cue.set("START", f"{pos:.6f}")
                cue.set("LEN", "0.000000")
                cue.set("REPEATS", "-1")
                cue.set("HOTCUE", str(num))
    tree = ET.ElementTree(root)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tree.write(output_path, encoding="utf-8", xml_declaration=True)


# Traktor MUSICAL_KEY VALUE 0-23 → Camelot notation
_TRAKTOR_KEY_MAP = [
    "1B", "2B", "3B", "4B", "5B", "6B", "7B", "8B", "9B", "10B", "11B", "12B",
    "9A", "10A", "11A", "12A", "1A", "2A", "3A", "4A", "5A", "6A", "7A", "8A",
]


def _traktor_key_to_camelot(value: str | None) -> str | None:
    if value is None:
        return None
    try:
        return _TRAKTOR_KEY_MAP[int(value)]
    except (ValueError, IndexError):
        return None


def parse_virtualdj_xml(path: Path) -> list[XmlTrack]:
    tree = ET.parse(path)
    root = tree.getroot()
    tracks: list[XmlTrack] = []
    for song in root.findall(".//Song"):
        file_path = song.get("FilePath") or ""
        hot_cues: list[tuple[int, float]] = []
        for poi in song.findall("Poi"):
            num = poi.get("Num")
            pos = poi.get("Pos")
            poi_type = poi.get("Type", "")
            if poi_type == "cue" and num is not None and pos is not None:
                try:
                    hot_cues.append((int(num), float(pos)))
                except (ValueError, TypeError):
                    pass
        tracks.append(
            XmlTrack(
                path=file_path,
                title=song.get("Title"),
                artist=song.get("Artist"),
                album=song.get("Album"),
                genre=song.get("Genre"),
                bpm=song.get("BPM"),
                key=song.get("Key"),
                hot_cues=hot_cues if hot_cues else None,
            )
        )
    return tracks
