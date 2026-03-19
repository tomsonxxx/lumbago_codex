from fastapi import APIRouter, Query, Depends
from typing import List, Optional
from .db import SessionLocal
from sqlalchemy import text
router = APIRouter(prefix='/api/tracks')

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get('/', summary='List tracks with filtering and search')
def list_tracks(q: Optional[str]=Query(None), bpm_min: Optional[int]=None, bpm_max: Optional[int]=None,
                key: Optional[str]=None, missing_metadata: Optional[bool]=False,
                skip: int=0, limit: int=100, sort: str='created_at', db=Depends(get_db)):
    # Basic SQL generation for flexibility (sqlite and pg compatible simple filters)
    base_sql = 'SELECT id, title, artist, bpm, key, duration, metadata FROM tracks WHERE 1=1'
    params = {}
    if q:
        base_sql += " AND (title LIKE :q OR artist LIKE :q)"
        params['q'] = f"%{q}%"
    if bpm_min is not None:
        base_sql += ' AND bpm >= :bpm_min'
        params['bpm_min'] = bpm_min
    if bpm_max is not None:
        base_sql += ' AND bpm <= :bpm_max'
        params['bpm_max'] = bpm_max
    if key:
        base_sql += ' AND key = :key'
        params['key'] = key
    if missing_metadata:
        base_sql += " AND (metadata IS NULL OR metadata = '')"
    # sort + limit
    if sort not in ('created_at','title','bpm'):
        sort = 'created_at'
    base_sql += f' ORDER BY {sort} LIMIT :limit OFFSET :skip'
    params['limit'] = limit
    params['skip'] = skip
    try:
        rows = db.execute(text(base_sql), params).fetchall()
        out = []
        for r in rows:
            out.append({'id': r[0], 'title': r[1], 'artist': r[2], 'bpm': r[3], 'key': r[4], 'duration': r[5], 'metadata': r[6]})
        return out
    except Exception as e:
        return {'error': str(e)}
