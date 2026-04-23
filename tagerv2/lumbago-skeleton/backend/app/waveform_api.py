from fastapi import APIRouter, HTTPException, Depends
from .db import SessionLocal
import subprocess, os
router = APIRouter(prefix='/api/waveform')

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post('/generate')
def generate_waveform(body: dict, db=Depends(get_db)):
    track_id = body.get('track_id')
    if not track_id:
        raise HTTPException(status_code=400, detail='track_id required')
    try:
        res = db.execute('SELECT id, title, metadata FROM tracks WHERE id = ?', (track_id,)).fetchone()
        if not res:
            raise HTTPException(status_code=404, detail='track not found')
        # assume storage path in metadata: metadata['storage_path']
        metadata = res[2] or '{}'
        try:
            import json
            meta = json.loads(metadata)
        except Exception:
            meta = {}
        audio_path = meta.get('storage_path')
        if not audio_path or not os.path.exists(audio_path):
            # Can't generate waveform without local file; in prod, pull from object storage
            raise HTTPException(status_code=400, detail='audio file not available on server')
        outdir = os.path.join(os.getcwd(), 'backend', 'waveforms')
        os.makedirs(outdir, exist_ok=True)
        outpath = os.path.join(outdir, f'waveform_{track_id}.png')
        # call the script
        script = os.path.join(os.getcwd(), 'scripts', 'generate_waveform.py')
        subprocess.run([sys.executable if 'sys' in globals() else 'python3', script, audio_path, outpath], check=False)
        # update DB
        db.execute('UPDATE tracks SET waveform_path = ? WHERE id = ?', (outpath, track_id))
        db.commit()
        return {'waveform_path': outpath}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
