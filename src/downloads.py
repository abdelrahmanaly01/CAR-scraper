"""Stream a property's ZIP to disk, validate it, then atomically publish it."""
import os
from pathlib import Path
import tempfile
import urllib.request
import zipfile

from .car_api import BASE_URL


def download_zip(id_origin, destination, progress=lambda received, total: None):
    if type(id_origin) is not int or id_origin <= 0:
        raise ValueError('Missing or invalid property download identifier.')
    destination = Path(destination)
    temporary = None
    try:
        url = f'{BASE_URL}/api/downloadBase/getShapeByIdOrigin/{id_origin}'
        with urllib.request.urlopen(url, timeout=60) as response:
            if response.status != 200:
                raise RuntimeError(f'Download returned HTTP {response.status}.')
            total = int(response.headers.get('Content-Length') or 0)
            received = 0
            with tempfile.NamedTemporaryFile(dir=destination.parent, prefix='.car-', suffix='.part', delete=False) as target:
                temporary = Path(target.name)
                while chunk := response.read(64 * 1024):
                    target.write(chunk)
                    received += len(chunk)
                    progress(received, total)
                target.flush()
                os.fsync(target.fileno())
            if total and received != total:
                raise RuntimeError('Incomplete download. Please try again.')
        with zipfile.ZipFile(temporary) as archive:
            if not archive.infolist() or archive.testzip() is not None:
                raise RuntimeError('The downloaded ZIP failed validation.')
        os.replace(temporary, destination)
        return destination
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
