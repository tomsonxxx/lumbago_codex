"""
Integration test: Web MVP — pełny przepływ edycji tagów przez API.

Testuje scenariusz:
  1. Import pliku audio do biblioteki (preview → commit)
  2. Odczyt z GET /tracks — weryfikacja że track jest w bazie
  3. Edycja tagów przez PUT /tracks/{path}
  4. Ponowny odczyt — weryfikacja że zmiany persystują w bazie
  5. Czyszczenie pola (pusty string) — weryfikacja zachowania backend

Nie wymaga prawdziwych plików audio — używa fake MP3 (4 bajty nagłówka).
"""
from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from lumbago_app.data.db import reset_engine
from web.backend.api import app


@pytest.fixture()
def client(monkeypatch, tmp_path: Path):
    """TestClient z izolowaną bazą danych w tmp_path."""
    monkeypatch.setenv("APPDATA", str(tmp_path))
    monkeypatch.setenv("WEB_BACKEND_DB", str(tmp_path / "web.sqlite3"))
    reset_engine()
    yield TestClient(app)
    reset_engine()


@pytest.fixture()
def imported_track(client: TestClient, tmp_path: Path) -> dict:
    """Importuje jeden fake MP3 i zwraca jego JSON z GET /tracks."""
    music_dir = tmp_path / "music"
    music_dir.mkdir()
    # Minimalne fake MP3 — wystarczy do skanowania ścieżki
    fake_mp3 = music_dir / "DJ Test - Sample Track.mp3"
    fake_mp3.write_bytes(b"\xff\xfb\x90\x00")  # MP3 frame header

    preview = client.post(
        "/tracks/import-preview",
        json={"folder": str(music_dir), "recursive": True},
    )
    assert preview.status_code == 200, preview.text
    assert len(preview.json()["tracks"]) == 1

    commit = client.post(
        "/tracks/import-commit",
        json={"paths": [str(fake_mp3)]},
    )
    assert commit.status_code == 200, commit.text
    assert commit.json()["imported"] == 1

    tracks = client.get("/tracks")
    assert tracks.status_code == 200
    stored = tracks.json()["tracks"]
    assert len(stored) == 1
    return stored[0]


class TestImportFlow:
    def test_import_preview_returns_tracks(self, client: TestClient, tmp_path: Path):
        """Import preview zwraca listę tracków z folderu."""
        music_dir = tmp_path / "music2"
        music_dir.mkdir()
        (music_dir / "Artysta - Tytul.mp3").write_bytes(b"\xff\xfb\x90\x00")

        r = client.post(
            "/tracks/import-preview",
            json={"folder": str(music_dir), "recursive": True},
        )
        assert r.status_code == 200
        tracks = r.json()["tracks"]
        assert len(tracks) == 1
        assert tracks[0]["path"].endswith(".mp3")

    def test_commit_persists_to_db(self, imported_track: dict):
        """Po imporcie track jest dostępny przez GET /tracks."""
        assert imported_track["id"] > 0
        assert imported_track["path"].endswith(".mp3")

    def test_import_empty_folder(self, client: TestClient, tmp_path: Path):
        """Import z pustego folderu zwraca pustą listę bez błędu."""
        empty = tmp_path / "empty"
        empty.mkdir()
        r = client.post(
            "/tracks/import-preview",
            json={"folder": str(empty), "recursive": True},
        )
        assert r.status_code == 200
        assert r.json()["tracks"] == []


class TestTagEditFlow:
    def test_put_updates_genre(self, client: TestClient, imported_track: dict):
        """PUT /tracks/{path} aktualizuje gatunek i persystuje."""
        path = imported_track["path"]
        r = client.put(f"/tracks/{path}", json={"genre": "Techno"})
        assert r.status_code == 200, r.text

        updated = r.json()["track"]
        assert updated["genre"] == "Techno"

        # Ponowny odczyt z bazy
        tracks = client.get("/tracks").json()["tracks"]
        assert tracks[0]["genre"] == "Techno"

    def test_put_updates_multiple_fields(self, client: TestClient, imported_track: dict):
        """PUT aktualizuje kilka pól jednocześnie."""
        path = imported_track["path"]
        r = client.put(
            f"/tracks/{path}",
            json={"genre": "House", "year": "2024", "bpm": 128.0, "key": "8A"},
        )
        assert r.status_code == 200, r.text
        updated = r.json()["track"]
        assert updated["genre"] == "House"
        assert updated["year"] == "2024"
        assert updated["bpm"] == pytest.approx(128.0)
        assert updated["key"] == "8A"

    def test_put_empty_string_clears_field(self, client: TestClient, imported_track: dict):
        """PUT z pustym stringiem "" czyści wartość (nie jest ignorowane jak None)."""
        path = imported_track["path"]

        # Najpierw ustaw gatunek
        client.put(f"/tracks/{path}", json={"genre": "Drum and Bass"})
        assert client.get("/tracks").json()["tracks"][0]["genre"] == "Drum and Bass"

        # Wyczyść pustym stringiem — backend używa exclude_none=True,
        # więc null byłby zignorowany, ale "" jest akceptowane
        r = client.put(f"/tracks/{path}", json={"genre": ""})
        assert r.status_code == 200, r.text

        tracks = client.get("/tracks").json()["tracks"]
        # Pole powinno być puste/None po wyczyszczeniu
        assert tracks[0].get("genre", "") in ("", None)

    def test_put_null_is_ignored(self, client: TestClient, imported_track: dict):
        """PUT z null ignoruje pole (nie nadpisuje istniejącej wartości)."""
        path = imported_track["path"]

        # Ustaw year
        client.put(f"/tracks/{path}", json={"year": "2023"})

        # Wyślij null dla year — powinien być zignorowany przez exclude_none=True
        r = client.put(f"/tracks/{path}", json={"genre": "Techno", "year": None})
        assert r.status_code == 200, r.text

        tracks = client.get("/tracks").json()["tracks"]
        track = tracks[0]
        assert track["genre"] == "Techno"
        assert track.get("year") == "2023"  # nie zmieniony

    def test_put_nonexistent_track_returns_404(self, client: TestClient):
        """PUT na nieistniejącą ścieżkę zwraca 404."""
        r = client.put("/tracks/C:/nonexistent/track.mp3", json={"genre": "Jazz"})
        assert r.status_code == 404
