"""AI service - Celery tasks and orchestration (skeleton)
Uwaga: wymaga uruchomienia Celery worker i brokera Redis/RabbitMQ.
"""
from celery import Celery
import time
from .db import SessionLocal
from .models_sql import Track
from uuid import uuid4
import os, json

CELERY_BROKER = os.getenv('CELERY_BROKER', 'redis://localhost:6379/0')
CELERY_BACKEND = os.getenv('CELERY_BACKEND', 'redis://localhost:6379/1')

celery = Celery('lumbago_ai', broker=CELERY_BROKER, backend=CELERY_BACKEND)

@celery.task(bind=True)
def analyze_track_task(self, track_id, ops=None):
    """Główny task analizy pliku audio.
    ops: dict np. { 'fingerprint': True, 'features': True, 'bpm': True, 'key': True, 'tagger': True }
    """
    db = SessionLocal()
    track = db.query(Track).get(track_id)
    if not track:
        return {'error': 'track_not_found'}
    # symulacja pracy
    progress = 0
    def set_progress(p):
        nonlocal progress
        progress = p
        try:
            self.update_state(state='PROGRESS', meta={'progress': progress})
        except Exception:
            pass
    try:
        if ops is None:
            ops = {'fingerprint': True, 'features': True, 'bpm': True, 'key': True, 'tagger': True}
        # 1. fingerprint
        if ops.get('fingerprint'):
            set_progress(10)
            time.sleep(1)
            track.fingerprint = f"fp_{uuid4().hex[:16]}"
            db.commit()
        # 2. features
        if ops.get('features'):
            set_progress(40)
            time.sleep(1)
            track.metadata = track.metadata or {}
            track.metadata['features'] = {'mfcc_sample': [0.1,0.2,0.3]}
            db.commit()
        # 3. bpm/key
        if ops.get('bpm'):
            set_progress(60)
            time.sleep(1)
            track.bpm = track.bpm or 120
            db.commit()
        if ops.get('key'):
            set_progress(75)
            time.sleep(1)
            track.key = track.key or '9A'
            db.commit()
        # 4. tagger (mock)
        if ops.get('tagger'):
            set_progress(90)
            time.sleep(1)
            track.metadata = track.metadata or {}
            track.metadata['ai_tags'] = {'genre': 'Deep House', 'mood': 'Energetic', 'confidence': 0.82}
            db.commit()
        set_progress(100)
        return {'status': 'finished', 'track_id': track_id}
    except Exception as e:
        return {'error': str(e)}
