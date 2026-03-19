from fastapi import FastAPI, HTTPException, UploadFile, File, Depends
from pydantic import BaseModel
from typing import List
from .db import SessionLocal, init_db
from .models_sql import Track
from sqlalchemy.orm import Session
import os

app = FastAPI(title="Lumbago Music AI - Backend (skeleton)")
app.include_router(auth_router)
app.include_router(auth_router_full)
app.include_router(playlists_router)
from .duplicates_api import router as duplicates_router
app.include_router(duplicates_router)
from .tracks_api import router as tracks_router
app.include_router(tracks_router)
from .import_api import router as import_router
app.include_router(import_router)
from .waveform_api import router as waveform_router
app.include_router(waveform_router)
from .library_api import router as library_router
app.include_router(library_router)

# initialize sqlite for dev
if not os.path.exists('lumbago.db'):
    init_db()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class TrackIn(BaseModel):
    title: str
    artist: str = None
    bpm: int = None
    key: str = None
    duration: int = None

class TrackOut(TrackIn):
    id: int

@app.get('/health')
async def health():
    return {'status': 'ok', 'service': 'lumbago-backend'}

@app.get('/version')
async def version():
    return {'version': '0.0.1'}

@app.post('/api/tracks', response_model=TrackOut)
async def create_track(track: TrackIn, db: Session = Depends(get_db)):
    db_track = Track(**track.dict())
    db.add(db_track)
    db.commit()
    db.refresh(db_track)
    return TrackOut(id=db_track.id, **track.dict())

@app.get('/api/tracks', response_model=List[TrackOut])
async def list_tracks(q: str = None, bpm_min: int = None, bpm_max: int = None, key: str = None, missing_metadata: bool = False, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    tracks = db.query(Track).offset(skip).limit(limit).all()
    return [TrackOut(id=t.id, title=t.title, artist=t.artist, bpm=t.bpm, key=t.key, duration=t.duration) for t in tracks]

@app.get('/api/tracks/{track_id}', response_model=TrackOut)
async def get_track(track_id: int, db: Session = Depends(get_db)):
    t = db.query(Track).filter(Track.id == track_id).first()
    if not t:
        raise HTTPException(status_code=404, detail='Track not found')
    return TrackOut(id=t.id, title=t.title, artist=t.artist, bpm=t.bpm, key=t.key, duration=t.duration)

@app.post('/api/tracks/upload')
async def upload_track(file: UploadFile = File(...)):
    uploads_dir = 'uploads'
    os.makedirs(uploads_dir, exist_ok=True)
    path = os.path.join(uploads_dir, file.filename)
    with open(path, 'wb') as f:
        content = await file.read()
        f.write(content)
    return {'filename': file.filename, 'size': len(content)}

from pydantic import BaseModel
from .ai_service import analyze_track_task

class AnalyzeRequest(BaseModel):
    track_id: int
    ops: dict = {}

@app.post('/api/ai/analyze')
async def analyze(req: AnalyzeRequest):
    job = analyze_track_task.apply_async(args=(req.track_id, req.ops))
    return {'job_id': job.id}

@app.get('/api/ai/jobs/{job_id}')
async def job_status(job_id: str):
    res = analyze_track_task.AsyncResult(job_id)
    status = res.status
    result = res.result if res.ready() else None
    return {'job_id': job_id, 'status': status, 'result': result}
