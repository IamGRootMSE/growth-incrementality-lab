"""Acquire immutable official Criteo v2.1; never silently synthesize data."""
import argparse
import hashlib
import json
import urllib.request
from pathlib import Path

URL = 'https://huggingface.co/datasets/criteo/criteo-uplift/resolve/main/criteo-research-uplift-v2.1.csv.gz'
SHA256 = '2716e1bf0fd157a93b5bf86924d9088419dfbac2022c6cd90030220634f616dc'

def digest(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()

def acquire(path=Path('data/raw/criteo-v2.1.csv.gz')):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        temporary = path.with_suffix('.partial')
        print('Downloading official Criteo v2.1...', flush=True)
        urllib.request.urlretrieve(URL, temporary)
        if digest(temporary) != SHA256:
            raise ValueError('Source checksum mismatch; do not use unverified data')
        temporary.replace(path)
    if digest(path) != SHA256:
        raise ValueError('Source checksum mismatch')
    print(json.dumps({'path': str(path), 'sha256': SHA256, 'bytes': path.stat().st_size}))
    return path

if __name__ == '__main__':
    acquire()
