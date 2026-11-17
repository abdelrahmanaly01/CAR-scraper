import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from src.diagnostics import SessionDiagnostics, classify


class DiagnosticsTests(unittest.TestCase):
    def test_restricted_endpoints(self):
        self.assertEqual(classify('https://consulta.car.gov.br/api/hcaptcha/validate?token=secret'), 'site_validation')
        self.assertEqual(classify('https://www.google.com/recaptcha/api2/userverify?k=secret'), 'recaptcha_userverify')
        self.assertIsNone(classify('https://example.com/recaptcha/api2/userverify'))
        self.assertIsNone(classify('https://consulta.car.gov.br/api/totalizer/getDetailsByCoordinates?lat=1'))

    def test_tokens_and_urls_not_logged(self):
        with tempfile.TemporaryDirectory() as directory:
            logger = SessionDiagnostics(Path(directory))
            url = 'https://consulta.car.gov.br/api/hcaptcha/validate?token=SUPERSECRET'
            logger.request(SimpleNamespace(url=url, method='POST', post_data='SUPERSECRET'))
            logger.response(SimpleNamespace(url=url, status=403))
            logger.failed(SimpleNamespace(url=url, failure='net::ERR_FAILED SUPERSECRET'))
            content = logger.path.read_text()
            self.assertNotIn('SUPERSECRET', content)
            self.assertNotIn('https://', content)
            self.assertIn('site_validation', content)
            self.assertIn('403', content)
