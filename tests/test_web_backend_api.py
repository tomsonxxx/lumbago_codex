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
