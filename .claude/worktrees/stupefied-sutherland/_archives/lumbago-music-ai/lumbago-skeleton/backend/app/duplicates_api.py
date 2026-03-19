from fastapi import APIRouter, Depends
from .db import SessionLocal
from .duplicate_finder import find_duplicates
from sqlalchemy.orm import Session

router = APIRouter(prefix='/api/duplicates')

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post('/find')
def find_route(scope: dict = None, db: Session = Depends(get_db)):
    # For skeleton: load tracks from DB and pass to find_duplicates
    # Here we mock with a small dataset if DB empty
    tracks = []
    try:
        rows = db.execute('SELECT id, title, artist, duration, fingerprint FROM tracks').fetchall()
        for r in rows:
            tracks.append({'id': r[0], 'title': r[1], 'artist': r[2], 'duration': r[3], 'fingerprint': r[4]})
    except Exception:
        # fallback mock
        tracks = [
            {'id':1,'title':'Deep Voyage','artist':'DJ Tom','duration':372,'file_hash':'abc123','fingerprint':'fp_aaaa'},
            {'id':2,'title':'Deep Voyage','artist':'DJ Tom','duration':372,'file_hash':'abc123','fingerprint':'fp_aaaa'},
        ]
    groups = find_duplicates(tracks)
    # Map groups to simple JSON
    out = []
    for g in groups:
        out.append({'tracks': [{'id':t.get('id'), 'title':t.get('title'), 'artist':t.get('artist')} for t in g['tracks']], 'matches': g['matches']})
    return out
