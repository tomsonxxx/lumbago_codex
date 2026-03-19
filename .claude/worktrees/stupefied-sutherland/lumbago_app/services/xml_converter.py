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
        tracks.append(
            XmlTrack(
                path=location,
                title=track_node.get("Name"),
                artist=track_node.get("Artist"),
                album=track_node.get("Album"),
                genre=track_node.get("Genre"),
                bpm=track_node.get("BPM"),
                key=track_node.get("Key"),
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
