from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from .db import SessionLocal
from .models_playlists import Playlist
from sqlalchemy.orm import Session

router = APIRouter(prefix='/api/playlists')

class PlaylistIn(BaseModel):
    name: str
    description: str = None

@router.post('/', response_model=PlaylistIn)
def create_playlist(p: PlaylistIn, db: Session = Depends(lambda: SessionLocal())):
    pl = Playlist(name=p.name, description=p.description)
    db.add(pl); db.commit(); db.refresh(pl)
    return {'name': pl.name, 'description': pl.description}

@router.get('/')
def list_playlists(skip: int = 0, limit: int = 100, db: Session = Depends(lambda: SessionLocal())):
    pls = db.query(Playlist).offset(skip).limit(limit).all()
    return [{'id': pl.id, 'name': pl.name, 'description': pl.description} for pl in pls]
