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


from dataclasses import dataclass as _dc
from pathlib import Path as _Path
import xml.etree.ElementTree as _ET

@_dc
class XmlCuePoint:
    name: str = "Cue"
    position_ms: float = 0.0
    cue_type: int = 0
    num: int = -1
    end_ms: float | None = None
    red: int = 40; green: int = 226; blue: int = 20

def _ms_to_s(ms: float) -> str: return f"{ms/1000:.3f}"

def export_rekordbox_xml_with_cues(tracks_with_cues: list[tuple[dict,list]], output_path, collection_name: str = "Lumbago_Music") -> None:
    root = _ET.Element("DJ_PLAYLISTS", {"Version":"1.0.0"})
    _ET.SubElement(root,"PRODUCT",{"Name":"Lumbago_Music","Version":"2.0","Company":"Lumbago"})
    col = _ET.SubElement(root,"COLLECTION",{"Entries":str(len(tracks_with_cues))})
    for i,(td,cues) in enumerate(tracks_with_cues, 1):
        path = td.get("path","")
        uri = _Path(path).as_uri() if path else ""
        te = _ET.SubElement(col,"TRACK",{
            "TrackID":str(i),"Name":str(td.get("title") or ""),"Artist":str(td.get("artist") or ""),
            "Album":str(td.get("album") or ""),"Genre":str(td.get("genre") or ""),"Year":str(td.get("year") or ""),
            "Bpm":f"{float(td.get('bpm') or 0):.2f}","Tonality":str(td.get("key") or ""),
            "Location":uri,"TotalTime":str(int(float(td.get("duration") or 0))),
            "Rating":str(int(td.get("rating") or 0)*51),
        })
        for cue in cues:
            if not isinstance(cue, XmlCuePoint):
                color = getattr(cue,'color',"#28e214").lstrip("#")
                try: r,g,b = int(color[0:2],16),int(color[2:4],16),int(color[4:6],16)
                except: r,g,b = 40,226,20
                tm = {"hotcue":0,"fade_in":1,"fade_out":2,"load":3,"loop":4}
                ct = tm.get(getattr(cue,'cue_type',"hotcue"),0)
                cue = XmlCuePoint(name=getattr(cue,'label',None) or "Cue",
                    position_ms=float(getattr(cue,'time_ms',0)), cue_type=ct,
                    num=getattr(cue,'hotcue_index',-1) if ct==0 else -1,
                    end_ms=float(cue.loop_end_ms) if ct==4 and getattr(cue,'loop_end_ms',None) else None,
                    red=r,green=g,blue=b)
            att = {"Name":cue.name,"Type":str(cue.cue_type),"Start":_ms_to_s(cue.position_ms),"Num":str(cue.num),"Red":str(cue.red),"Green":str(cue.green),"Blue":str(cue.blue)}
            if cue.end_ms is not None and cue.cue_type==4: att["End"]=_ms_to_s(cue.end_ms)
            te.append(_ET.Element("POSITION_MARK", att))
    _ET.indent(root, space="  ")
    op = _Path(output_path); op.parent.mkdir(parents=True, exist_ok=True)
    _ET.ElementTree(root).write(str(op), encoding="utf-8", xml_declaration=True)

def import_rekordbox_cues(xml_path) -> dict[str,list]:
    result: dict[str,list] = {}
    try: tree = _ET.parse(str(xml_path)); root = tree.getroot()
    except Exception as e: return result
    for te in root.iter("TRACK"):
        loc = te.get("Location","")
        if not loc: continue
        from urllib.parse import unquote
        fp = unquote(loc[7:]) if loc.startswith("file:///") else loc
        cues = []
        for pm in te.findall("POSITION_MARK"):
            try:
                es = pm.get("End"); cues.append(XmlCuePoint(name=pm.get("Name","Cue"),
                    position_ms=float(pm.get("Start","0"))*1000,cue_type=int(pm.get("Type","0")),
                    num=int(pm.get("Num","-1")),end_ms=float(es)*1000 if es else None,
                    red=int(pm.get("Red","40")),green=int(pm.get("Green","226")),blue=int(pm.get("Blue","20"))))
            except Exception: pass
        if cues: result[fp] = cues
    return result

def import_vdj_cues(xml_path) -> dict[str,list]:
    result: dict[str,list] = {}
    try: tree = _ET.parse(str(xml_path)); root = tree.getroot()
    except Exception: return result
    tm = {"cue":0,"fade_in":1,"fade_out":2,"automix":3,"loop":4}
    for song in root.iter("Song"):
        fp = song.get("Filepath","")
        if not fp: continue
        cues = []
        for poi in song.findall("Poi"):
            try:
                n = poi.get("Num","-1"); cues.append(XmlCuePoint(name=poi.get("Name","Cue"),
                    position_ms=float(poi.get("Pos","0"))*1000,
                    cue_type=tm.get(poi.get("Type","cue").lower(),0),
                    num=int(n) if n.lstrip("-").isdigit() else -1))
            except Exception: pass
        if cues: result[fp] = cues
    return result

def sync_rekordbox_cues_to_domain(xml_cues: dict[str,list]) -> dict[str,list]:
    from core.models import CuePoint
    result: dict[str,list] = {}
    for fp, xcues in xml_cues.items():
        dm = []
        for xc in xcues:
            color = f"#{xc.red:02x}{xc.green:02x}{xc.blue:02x}"
            tm = {0:"hotcue",1:"fade_in",2:"fade_out",3:"load",4:"loop"}
            dm.append(CuePoint(time_ms=int(xc.position_ms),cue_type=tm.get(xc.cue_type,"hotcue"),
                hotcue_index=xc.num if xc.num>=0 else None,
                loop_end_ms=int(xc.end_ms) if xc.end_ms else None,label=xc.name,color=color))
        result[fp] = dm
    return result
