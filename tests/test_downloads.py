import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from src.downloads import download_zip


class Response(io.BytesIO):
    status = 200

    def __init__(self, data, length=None):
        super().__init__(data)
        self.headers = {'Content-Length': str(len(data) if length is None else length)}


class DownloadTests(unittest.TestCase):
    def test_valid_zip_saved_with_progress(self):
        data = io.BytesIO()
        with zipfile.ZipFile(data, 'w') as archive:
            archive.writestr('example.txt', 'test data')
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'property.zip'
            updates = []
            with patch('src.downloads.urllib.request.urlopen', return_value=Response(data.getvalue())) as request:
                download_zip(5114292, path, lambda n, total: updates.append((n, total)))
            self.assertEqual(path.read_bytes(), data.getvalue())
            self.assertEqual(updates[-1], (len(data.getvalue()), len(data.getvalue())))
            self.assertIn('/5114292', request.call_args.args[0])
            self.assertEqual(list(Path(folder).iterdir()), [path])

    def test_error_response_preserves_existing_file_and_cleans_partial(self):
        for response in (Response(b'<html>error</html>'), Response(b'partial', 100)):
            with self.subTest(response=response), tempfile.TemporaryDirectory() as folder:
                path = Path(folder) / 'property.zip'
                path.write_bytes(b'existing file')
                with patch('src.downloads.urllib.request.urlopen', return_value=response):
                    with self.assertRaises((RuntimeError, zipfile.BadZipFile)):
                        download_zip(5114292, path)
                self.assertEqual(path.read_bytes(), b'existing file')
                self.assertEqual(list(Path(folder).iterdir()), [path])

    def test_invalid_identifier_never_requests(self):
        with patch('src.downloads.urllib.request.urlopen') as request:
            with self.assertRaises(ValueError):
                download_zip(None, 'unused.zip')
        request.assert_not_called()
