from sqlalchemy import Column, Integer, String, Float, DateTime, JSON
from datetime import datetime
from .db import Base

class Track(Base):
    __tablename__ = 'tracks'
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False, default='Untitled')
    artist = Column(String, nullable=True)
    bpm = Column(Integer, nullable=True)
    key = Column(String, nullable=True)
    duration = Column(Integer, nullable=True)
    fingerprint = Column(String, nullable=True)
    waveform_path = Column(String, nullable=True)
    features = Column(JSON, nullable=True)
    ai_tags = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
