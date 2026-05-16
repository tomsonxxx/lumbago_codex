from __future__ import annotations

from core.models import AnalysisResult, Track
from services.ai_tagger import CloudAiTagger, _sanitize_prompt_value


class _FakeResponse:
    status_code = 200
    ok = True
    reason = "OK"
    text = "{}"

    def __init__(self, payload: dict):
        self._payload = payload
        self.text = str(payload)

    def json(self) -> dict:
        return self._payload

    def raise_for_status(self) -> None:
        return None


def test_sanitize_prompt_value_masks_urls_paths_and_binary_blobs() -> None:
    raw = (
        "Artist https://example.com C:\\Music\\set\\track.mp3 /home/user/music/a.mp3 "
        + ("A" * 320)
    )
    cleaned = _sanitize_prompt_value(raw)
    assert "https://example.com" not in cleaned
    assert "C:\\Music\\set\\track.mp3" not in cleaned
    assert "/home/user/music/a.mp3" not in cleaned
    assert "[URL]" in cleaned
    assert "[PATH]" in cleaned

    binary_only = _sanitize_prompt_value("A" * 350)
    assert binary_only == "[BINARY_OMITTED]"


def test_analyze_batch_sends_one_sanitized_album_context_request(monkeypatch) -> None:
    calls: list[dict] = []

    def _fake_post(url, headers=None, json=None, timeout=None):
        calls.append(json)
        return _FakeResponse(
            {
                "choices": [
                    {
                        "message": {
                            "content": (
                                "["
                                '{"originalFilename":"01-intro.mp3","tags":{"title":"Intro",'
                                '"artist":"Artist","album":"Shared Album","albumArtist":"Artist",'
                                '"trackNumber":"1"}},'
                                '{"originalFilename":"02-main.mp3","tags":{"title":"Main",'
                                '"artist":"Artist","album":"Shared Album","albumArtist":"Artist",'
                                '"trackNumber":"2"}}'
                                "]"
                            )
                        }
                    }
                ]
            }
        )

    monkeypatch.setattr("requests.post", _fake_post)
    monkeypatch.setattr("time.sleep", lambda _s: None)
    tagger = CloudAiTagger(
        provider="openai",
        api_key="x",
        base_url="https://example.test/v1",
        model="demo",
    )
    long_comment = "liner notes " + ("very long " * 80) + "APIC hidden cover"
    tracks = [
        Track(
            path=r"C:\Music\Artist\Album\01-intro.mp3",
            title="Intro",
            artist="Artist",
            album="Shared Album",
            comment=long_comment,
            artwork_path=r"C:\Music\Artist\Album\cover.jpg",
        ),
        Track(path=r"C:\Music\Artist\Album\02-main.mp3", title="Main", artist="Artist"),
    ]

    results = tagger.analyze_batch(tracks, chunk_size=20)

    assert len(calls) == 1
    prompt = calls[0]["messages"][1]["content"]
    assert "01-intro.mp3" in prompt
    assert "02-main.mp3" in prompt
    assert '"folder": "Album"' in prompt
    assert "albumCoverUrl" not in prompt
    assert "picture" not in prompt
    assert "APIC hidden cover" not in prompt
    assert len(prompt) < 5000
    assert [result.title for result in results] == ["Intro", "Main"]
    assert all(result.album == "Shared Album" for result in results)


def test_analyze_batch_harmonizes_album_fields_within_chunk(monkeypatch) -> None:
    tagger = CloudAiTagger(
        provider="openai",
        api_key="x",
        base_url="https://example.test/v1",
        model="demo",
    )
    tracks = [Track(path=f"{idx:02d}.mp3") for idx in range(3)]

    albums = ["Wrong Album", "Homework", "Homework"]

    def _fake_batch(chunk: list[Track]) -> list[AnalysisResult]:
        results: list[AnalysisResult] = []
        for track in chunk:
            idx = int(track.path.split(".")[0])
            results.append(
                AnalysisResult(album=albums[idx], artist="Daft Punk", albumartist="Daft Punk")
            )
        return results

    monkeypatch.setattr(tagger, "_analyze_batch_chunk", _fake_batch)
    monkeypatch.setattr("time.sleep", lambda _s: None)

    results = tagger.analyze_batch(tracks, chunk_size=20)

    assert len(results) == 3
    assert all(result.album == "Homework" for result in results)
    assert all(result.artist == "Daft Punk" for result in results)
    assert all(result.albumartist == "Daft Punk" for result in results)


def test_analyze_batch_enforces_cooldown_between_chunks(monkeypatch) -> None:
    tagger = CloudAiTagger(
        provider="openai",
        api_key="x",
        base_url="https://example.test/v1",
        model="demo",
    )
    tracks = [Track(path=f"{idx:02d}.mp3") for idx in range(30)]
    sleep_calls: list[float] = []

    # Mock at chunk level to avoid HTTP retries polluting the sleep trace.
    monkeypatch.setattr(tagger, "_analyze_batch_chunk", lambda chunk: [AnalysisResult() for _ in chunk])
    monkeypatch.setattr("services.ai_tagger.time.sleep", lambda s: sleep_calls.append(float(s)))

    results = tagger.analyze_batch(tracks, chunk_size=100)

    assert len(results) == 30
    assert sleep_calls == [3.5]
