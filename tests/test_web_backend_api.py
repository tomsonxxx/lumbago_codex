from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from web.backend.api import app


def test_web_backend_api_flow(tmp_path: Path, monkeypatch):
    db_path = tmp_path / "api.sqlite3"
    monkeypatch.setenv("WEB_BACKEND_DB", str(db_path))

    with TestClient(app) as client:
        assert client.get("/health").status_code == 200

        put_setting = client.put("/settings/theme", json={"value": "dark"})
        assert put_setting.status_code == 200
        assert put_setting.json()["value"] == "dark"

        get_setting = client.get("/settings/theme")
        assert get_setting.status_code == 200
        assert get_setting.json()["value"] == "dark"

        put_cache = client.put("/cache/track:1", json={"value": '{"title":"A"}', "ttl_seconds": 60})
        assert put_cache.status_code == 200

        get_cache = client.get("/cache/track:1")
        assert get_cache.status_code == 200
        assert get_cache.json()["value"] == '{"title":"A"}'

        post_history = client.post(
            "/tag-history",
            json={
                "track_id": 1,
                "field_name": "genre",
                "old_value": "house",
                "new_value": "techno",
                "source": "web",
            },
        )
        assert post_history.status_code == 200

        read_history = client.get("/tag-history/1")
        assert read_history.status_code == 200
        items = read_history.json()["items"]
        assert len(items) == 1
        assert items[0]["field_name"] == "genre"

