from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from lumbago_app.core.models import Track
from lumbago_app.services.free_music_portals import PortalCandidate, PortalProbe
from lumbago_app.services.recognition_pipeline_v2 import RecognitionPipelineV2, _build_portal_queries


@dataclass
class _StubRecognizer:
    payload: dict | None

    def recognize(self, _audio_path: Path):
        return self.payload


@dataclass
class _StubMusicBrainzProvider:
    recording: dict | None

    def get_recording(self, _mbid: str):
        return self.recording


@dataclass
class _StubPortalSearch:
    probes: list[PortalProbe]
    raise_error: Exception | None = None

    def search_all(self, _query: str):
        if self.raise_error is not None:
            raise self.raise_error
        return self.probes


def test_fingerprint_evidence_wins_over_portal_and_filename(tmp_path):
    audio = tmp_path / "Hardwell - Wrong Title.mp3"
    audio.write_bytes(b"fake audio")
    track = Track(path=str(audio), title="Wrong Title", artist="Hardwell")

    recognizer = _StubRecognizer(
        {
            "results": [
                {
                    "score": 0.95,
                    "recordings": [{"id": "mbid-1"}],
                }
            ]
        }
    )
    musicbrainz = _StubMusicBrainzProvider(
        {
            "title": "Children",
            "artist-credit": [{"name": "Tiesto"}],
            "releases": [
                {
                    "title": "Just Be",
                    "date": "2004-04-06",
                    "artist-credit": [{"name": "Tiesto"}],
                    "label-info": [{"label": {"name": "Magik Muzik"}}],
                }
            ],
        }
    )
    portals = _StubPortalSearch(
        [
            PortalProbe(
                source_key="musicbrainz_portal",
                source_label="MusicBrainz",
                candidate=PortalCandidate(source_key="musicbrainz_portal", source_label="MusicBrainz", title="Different Song", artist="Different Artist"),
                detail="OK",
            )
        ]
    )

    result = RecognitionPipelineV2(
        recognizer=recognizer,
        musicbrainz_provider=musicbrainz,
        portal_search=portals,
    ).recognize_track(track)

    assert result.primary_source == "acoustid"
    assert any(evidence.value == "Children" and evidence.source == "acoustid" for evidence in result.evidence_by_field["title"])
    assert any(evidence.value == "Tiesto" and evidence.source == "acoustid" for evidence in result.evidence_by_field["artist"])
    assert any(attempt.source == "acoustid" and attempt.status == "hit" for attempt in result.attempts)
    assert "acoustid" in result.summary


def test_pipeline_falls_back_to_portal_when_fingerprint_missing(tmp_path):
    audio = tmp_path / "Unknown Artist - Mystery Track.mp3"
    audio.write_bytes(b"fake audio")
    track = Track(path=str(audio), title=None, artist=None)

    portals = _StubPortalSearch(
        [
            PortalProbe(
                source_key="musicbrainz_portal",
                source_label="MusicBrainz",
                candidate=PortalCandidate(
                    source_key="musicbrainz_portal",
                    source_label="MusicBrainz",
                    title="Mystery Track",
                    artist="Unknown Artist",
                    album="Mystery EP",
                ),
                detail="OK",
            )
        ]
    )

    result = RecognitionPipelineV2(
        recognizer=_StubRecognizer(payload=None),
        musicbrainz_provider=_StubMusicBrainzProvider(recording=None),
        portal_search=portals,
    ).recognize_track(track)

    assert result.primary_source == "musicbrainz_portal"
    assert any(evidence.source == "musicbrainz_portal" for evidence in result.evidence_by_field["title"])
    assert any(evidence.source == "musicbrainz_portal" for evidence in result.evidence_by_field["artist"])
    assert result.track.title == "Mystery Track"


def test_pipeline_repairs_incomplete_filename_without_network(tmp_path):
    audio = tmp_path / "Poylow, ATHYN - Good In Goodbye - 320.mp3"
    audio.write_bytes(b"fake audio")
    track = Track(path=str(audio), title="320", artist="Poylow ATHYN")

    result = RecognitionPipelineV2(
        recognizer=_StubRecognizer(payload=None),
        musicbrainz_provider=_StubMusicBrainzProvider(recording=None),
        portal_search=_StubPortalSearch(probes=[]),
    ).recognize_track(track)

    assert result.track.title == "Good In Goodbye"
    assert result.evidence_by_field["title"][0].source == "filename"
    assert result.filename_query is not None


def test_pipeline_survives_source_errors(tmp_path):
    audio = tmp_path / "Artist - Song.mp3"
    audio.write_bytes(b"fake audio")
    track = Track(path=str(audio), title=None, artist=None)

    result = RecognitionPipelineV2(
        recognizer=_StubRecognizer(payload=None),
        musicbrainz_provider=_StubMusicBrainzProvider(recording=None),
        portal_search=_StubPortalSearch(probes=[], raise_error=RuntimeError("portal down")),
    ).recognize_track(track)

    assert result.summary
    assert any(attempt.status in {"miss", "error"} for attempt in result.attempts)


def test_build_portal_queries_uses_filename_and_tag_permutations():
    track = Track(
        path=r"C:\music\01 - Tiesto - Children (Official Video) [HD] 320.mp3",
        title="Children - 320",
        artist="Tiesto",
        albumartist="Tiesto",
        remixer="Hardwell Remix",
        genre="Trance",
    )

    queries = _build_portal_queries(track)

    assert len(queries) >= 4
    assert any("tiesto" in query.lower() and "children" in query.lower() for query in queries)
    assert any("children" in query.lower() and "hardwell" in query.lower() for query in queries)
    assert all("official" not in query.lower() for query in queries)
    assert all("320" not in query.lower() for query in queries)


def test_pipeline_refresh_mode_clears_previous_metadata_before_rebuild(tmp_path):
    audio = tmp_path / "Mystery_File.mp3"
    audio.write_bytes(b"fake audio")
    track = Track(
        path=str(audio),
        title="Old Title",
        artist="Old Artist",
        album="Old Album",
        genre="Old Genre",
        comment="Old Comment",
        fingerprint="oldfp",
        artwork_path="old.jpg",
    )

    result = RecognitionPipelineV2(
        recognizer=_StubRecognizer(payload=None),
        musicbrainz_provider=_StubMusicBrainzProvider(recording=None),
        portal_search=_StubPortalSearch(probes=[]),
    ).recognize_track(track, refresh_existing=True)

    assert result.track.title == "Mystery File"
    assert result.track.artist is None
    assert result.track.album is None
    assert result.track.genre is None
    assert result.track.comment is None
    assert result.track.fingerprint is None
    assert result.track.artwork_path is None
