from fastapi import APIRouter, Depends, Query, HTTPException
from typing import List, Optional
from .db import SessionLocal
from .models_sql import Track
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from pydantic import BaseModel

router = APIRouter(prefix='/api/library')

class TrackOut(BaseModel):
    id: int
    title: str
    artist: Optional[str]
    bpm: Optional[int]
    key: Optional[str]
    duration: Optional[int]

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get('/tracks', response_model=List[TrackOut])
def list_tracks(q: Optional[str] = Query(None), bpm_min: Optional[int] = Query(None), bpm_max: Optional[int] = Query(None), key: Optional[str] = Query(None), missing_metadata: Optional[bool] = Query(False), skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    qs = db.query(Track)
    if q:
        qterm = f"%{q}%"
        qs = qs.filter(or_(Track.title.ilike(qterm), Track.artist.ilike(qterm)))
    if bpm_min is not None:
        qs = qs.filter(Track.bpm >= bpm_min)
    if bpm_max is not None:
        qs = qs.filter(Track.bpm <= bpm_max)
    if key:
        qs = qs.filter(Track.key == key)
    if missing_metadata:
        qs = qs.filter(or_(Track.artist == None, Track.title == None))
    rows = qs.offset(skip).limit(limit).all()
    return [TrackOut(id=r.id, title=r.title, artist=r.artist, bpm=r.bpm, key=r.key, duration=r.duration) for r in rows]

@router.get('/tracks/{track_id}', response_model=TrackOut)
def get_track(track_id: int, db: Session = Depends(get_db)):
    t = db.query(Track).filter(Track.id == track_id).first()
    if not t:
        raise HTTPException(status_code=404, detail='Track not found')
    return TrackOut(id=t.id, title=t.title, artist=t.artist, bpm=t.bpm, key=t.key, duration=t.duration)
