from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_health():
    r = client.get('/health')
    assert r.status_code == 200
    assert r.json()['status'] == 'ok'

def test_create_and_get_track():
    payload = {'title': 'Test Track', 'artist': 'Tester', 'bpm': 128}
    r = client.post('/api/tracks', json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data['title'] == 'Test Track'
    tid = data['id']
    r2 = client.get('/api/tracks')
    assert r2.status_code == 200
    assert any(t['id'] == tid for t in r2.json())
    r3 = client.get(f'/api/tracks/{tid}')
    assert r3.status_code == 200
    assert r3.json()['title'] == 'Test Track'
