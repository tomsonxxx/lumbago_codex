
from backend.app.scanner import scan_folder
import os, tempfile

def test_scan_folder_basic():
    with tempfile.TemporaryDirectory() as d:
        f = os.path.join(d, 'track.mp3')
        open(f,'w').close()
        out = scan_folder(d)
        assert len(out) == 1
        assert out[0]['filename'] == 'track.mp3'
