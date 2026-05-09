
import os, time

def scan_folder(path: str):
    results = []
    for root, dirs, files in os.walk(path):
        for f in files:
            if f.lower().endswith(('.mp3','.flac','.wav','.m4a')):
                results.append({
                    'filename': f,
                    'fullpath': os.path.join(root,f),
                    'status': 'ok'
                })
    return results
