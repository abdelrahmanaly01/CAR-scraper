"""Tests for repeated coordinate lookup attempts without contacting the CAR service."""
import io
import json
import unittest
from unittest.mock import patch

from src.candidate_search import search_candidates


class CandidateSearchTests(unittest.TestCase):
    def test_default_search_attempts_ten_coordinate_lookups(self):
        registration = 'PR-4107256-605F909883AA43049A3F13A649F9C99A'
        payload = json.dumps({
            'codeProperty': registration,
            'idOrigin': 123,
        }).encode()
        coordinate_urls = []
        progress = []

        def fake_urlopen(url, **kwargs):
            if '/api/totalizer/' in url:
                coordinate_urls.append(url)
                return io.BytesIO(payload)
            return io.BytesIO(b'')

        with patch('src.candidate_search.urllib.request.urlopen', side_effect=fake_urlopen):
            result = search_candidates(-23, -53, lambda current, total: progress.append((current, total)))

        self.assertEqual(len(coordinate_urls), 10)
        self.assertEqual(result['attempts'], 10)
        self.assertEqual(progress, [(current, 10) for current in range(1, 11)])


if __name__ == '__main__':
    unittest.main()
