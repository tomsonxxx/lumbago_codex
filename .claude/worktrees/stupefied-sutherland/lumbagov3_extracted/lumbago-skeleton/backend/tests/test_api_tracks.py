from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_create_and_query_tracks():
    # create tracks
    t1 = {'title':'Deep Voyage','artist':'DJ Tom','bpm':125,'key':'9A','duration':372}
    t2 = {'title':'Sunrise Groove','artist':'Chill Dept','bpm':110,'key':'7A','duration':311}
    r1 = client.post('/api/tracks', json=t1)
    r2 = client.post('/api/tracks', json=t2)
    assert r1.status_code == 200
    assert r2.status_code == 200

    # query by q
    r = client.get('/api/tracks', params={'q':'Deep'})
    assert r.status_code == 200
    data = r.json()
    assert any(d['title']=='Deep Voyage' for d in data)

    # filter by bpm range
    r = client.get('/api/tracks', params={'bpm_min':120,'bpm_max':130})
    data = r.json()
    assert any(d['title']=='Deep Voyage' for d in data)

    # filter by key
    r = client.get('/api/tracks', params={'key':'7A'})
    data = r.json()
    assert any(d['title']=='Sunrise Groove' for d in data)
