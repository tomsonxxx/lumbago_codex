
from fastapi import APIRouter
from .scanner import scan_folder

router = APIRouter(prefix='/api/import')

@router.post('/scan')
def scan_endpoint(body: dict):
    folder = body.get('folder')
    if not folder:
        return {'error': 'missing folder'}
    out = scan_folder(folder)
    return {'files': out, 'count': len(out)}
