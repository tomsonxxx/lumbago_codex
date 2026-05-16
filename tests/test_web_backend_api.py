from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from lumbago_app.data.db import reset_engine
from web.backend.api import app


def test_web_backend_api_end_to_end(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("APPDATA", str(tmp_path))
    monkeypatch.setenv("WEB_BACKEND_DB", str(tmp_path / "web.sqlite3"))
    reset_engine()
    client = TestClient(app)

    sample_dir = tmp_path / "music"
    sample_dir.mkdir()
    file_a = sample_dir / "Artist A - Sunrise.mp3"
    file_b = sample_dir / "Artist A - Sunrise Copy.mp3"
    file_a.write_bytes(b"fake audio a")
    file_b.write_bytes(b"fake audio b")

    assert client.get("/health").json() == {"status": "ok"}

    put_setting = client.put("/settings/theme", json={"value": "dark"})
    assert put_setting.status_code == 200
    assert client.get("/settings/theme").json()["value"] == "dark"

    preview = client.post("/tracks/import-preview", json={"folder": str(sample_dir), "recursive": True})
    assert preview.status_code == 200
    preview_tracks = preview.json()["tracks"]
    assert len(preview_tracks) == 2
    assert preview_tracks[0]["path"].endswith(".mp3")

    commit = client.post("/tracks/import-commit", json={"paths": [str(file_a), str(file_b)]})
    assert commit.status_code == 200
    assert commit.json()["imported"] == 2

    tracks = client.get("/tracks")
    assert tracks.status_code == 200
    stored = tracks.json()["tracks"]
    assert len(stored) == 2
    assert {item["title"] for item in stored} == {"Sunrise", "Sunrise Copy"}

    dup = client.post("/duplicates/analyze", json={"mode": "metadata"})
    assert dup.status_code == 200
    assert dup.json()["groups"] == []

    history_write = client.post(
        "/tag-history",
        json={
            "track_id": stored[0]["id"],
            "field_name": "genre",
            "old_value": "house",
            "new_value": "techno",
            "source": "web-test",
        },
    )
    assert history_write.status_code == 200

    history = client.get(f"/tag-history/{stored[0]['id']}")
    assert history.status_code == 200
    assert history.json()["items"][0]["field_name"] == "genre"

    reset_engine()


def _make_client(monkeypatch, tmp_path: Path) -> TestClient:
    monkeypatch.setenv("APPDATA", str(tmp_path))
    monkeypatch.setenv("WEB_BACKEND_DB", str(tmp_path / "web.sqlite3"))
    reset_engine()
    return TestClient(app)


def _import_files(client: TestClient, *files: Path) -> list[dict]:
    commit = client.post("/tracks/import-commit", json={"paths": [str(f) for f in files]})
    assert commit.status_code == 200
    return client.get("/tracks").json()["tracks"]


def test_web_backend_track_update(monkeypatch, tmp_path: Path):
    client = _make_client(monkeypatch, tmp_path)
    sample = tmp_path / "Daft Punk - One More Time.mp3"
    sample.write_bytes(b"fake mp3")

    stored = _import_files(client, sample)
    assert len(stored) == 1
    track = stored[0]
    assert track["title"] == "One More Time"

    resp = client.put(
        f"/tracks/{track['path']}",
        json={"genre": "Electronic", "bpm": 123.0, "mood": "energetic"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "track" in body
    updated = body["track"]
    assert updated["genre"] == "Electronic"
    assert updated["bpm"] == 123.0

    all_tracks = client.get("/tracks").json()["tracks"]
    assert all_tracks[0]["genre"] == "Electronic"
    assert all_tracks[0]["bpm"] == 123.0

    reset_engine()


def test_web_backend_delete_track(monkeypatch, tmp_path: Path):
    client = _make_client(monkeypatch, tmp_path)
    sample = tmp_path / "artist - song.mp3"
    sample.write_bytes(b"fake mp3")

    stored = _import_files(client, sample)
    assert len(stored) == 1
    path = stored[0]["path"]

    del_resp = client.delete(f"/tracks/{path}")
    assert del_resp.status_code == 200

    remaining = client.get("/tracks").json()["tracks"]
    assert remaining == []

    reset_engine()


def test_web_backend_duplicate_hash(monkeypatch, tmp_path: Path):
    client = _make_client(monkeypatch, tmp_path)
    content = b"identical audio content"
    file_a = tmp_path / "song_a.mp3"
    file_b = tmp_path / "song_b.mp3"
    file_a.write_bytes(content)
    file_b.write_bytes(content)

    stored = _import_files(client, file_a, file_b)
    assert len(stored) == 2
    assert stored[0]["hash"] == stored[1]["hash"]

    dup = client.post("/duplicates/analyze", json={"mode": "hash"})
    assert dup.status_code == 200
    groups = dup.json()["groups"]
    assert len(groups) == 1
    assert len(groups[0]["tracks"]) == 2

    reset_engine()
