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


def parse_virtualdj_xml(path: Path) -> list[XmlTrack]:
    tree = ET.parse(path)
    root = tree.getroot()
    tracks: list[XmlTrack] = []
    for song in root.findall(".//Song"):
        file_path = song.get("FilePath") or ""
        tracks.append(
            XmlTrack(
                path=file_path,
                title=song.get("Title"),
                artist=song.get("Artist"),
                album=song.get("Album"),
                genre=song.get("Genre"),
                bpm=song.get("BPM"),
                key=song.get("Key"),
            )
        )
    return tracks
