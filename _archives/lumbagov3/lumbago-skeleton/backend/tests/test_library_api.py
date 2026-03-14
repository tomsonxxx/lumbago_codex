from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.init_db import init_db
import os

client = TestClient(app)

def setup_module(module):
    # ensure DB exists and has at least one track
    init_db()
    # create a sample track via API
    payload = {'title':'Test Track X','artist':'Tester','bpm':128,'key':'9A','duration':300}
    r = client.post('/api/tracks', json=payload)
    assert r.status_code == 200

def test_list_tracks():
    r = client.get('/api/library/tracks')
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert any(t['title']=='Test Track X' for t in data)

def test_search_query():
    r = client.get('/api/library/tracks', params={'q':'Test Track X'})
    assert r.status_code == 200
    data = r.json()
    assert len(data) >= 1

def test_get_track():
    r = client.get('/api/library/tracks')
    tid = r.json()[0]['id']
    r2 = client.get(f'/api/library/tracks/{tid}')
    assert r2.status_code == 200
    assert r2.json()['id'] == tid
