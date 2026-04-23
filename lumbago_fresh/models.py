from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class Track:
    path: str
    title: str = ""
    artist: str = ""
    album: str = ""
    genre: str = ""
    year: str = ""
    duration: float = 0.0
    analyzed: bool = False
    source: str = "import"

    @property
    def filename(self) -> str:
        return Path(self.path).name

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "Track":
        return cls(
            path=str(raw.get("path", "")),
            title=str(raw.get("title", "")),
            artist=str(raw.get("artist", "")),
            album=str(raw.get("album", "")),
            genre=str(raw.get("genre", "")),
            year=str(raw.get("year", "")),
            duration=float(raw.get("duration", 0.0) or 0.0),
            analyzed=bool(raw.get("analyzed", False)),
            source=str(raw.get("source", "import")),
        )

