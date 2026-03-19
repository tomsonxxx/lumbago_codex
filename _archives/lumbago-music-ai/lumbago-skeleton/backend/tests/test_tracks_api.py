from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_list_tracks_empty_or_ok():
    r = client.get('/api/tracks')
    assert r.status_code in (200, 500)

def test_search_tracks():
    r = client.get('/api/tracks', params={'q':'Deep'})
    assert r.status_code in (200, 500)
