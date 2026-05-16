from __future__ import annotations

from lumbago_app.core.models import AnalysisResult, Track
from lumbago_app.services.ai_tagger import CloudAiTagger, _sanitize_prompt_value


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


def test_analyze_batch_harmonizes_album_fields_within_chunk(monkeypatch) -> None:
    tagger = CloudAiTagger(
        provider="openai",
        api_key="x",
        base_url="https://example.test/v1",
        model="demo",
    )
    tracks = [Track(path=f"{idx:02d}.mp3") for idx in range(3)]

    albums = ["Wrong Album", "Homework", "Homework"]

    def _fake_analyze(track: Track) -> AnalysisResult:
        idx = int(track.path.split(".")[0])
        return AnalysisResult(album=albums[idx], artist="Daft Punk", albumartist="Daft Punk")

    monkeypatch.setattr(tagger, "analyze", _fake_analyze)
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

    monkeypatch.setattr(tagger, "_analyze_batch_chunk", lambda chunk: [AnalysisResult() for _ in chunk])
    monkeypatch.setattr("time.sleep", lambda seconds: sleep_calls.append(float(seconds)))

    results = tagger.analyze_batch(tracks, chunk_size=100)

    assert len(results) == 30
    assert sleep_calls == [3.5]
