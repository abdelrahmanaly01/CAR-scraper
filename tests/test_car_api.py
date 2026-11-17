import unittest
from unittest.mock import Mock, patch
from src.car_api import lookup_property, PortalError, Property
from src.portal import verify_registration, open_property

CORRECT = 'PR-4107256-605F909883AA43049A3F13A649F9C99A'
WRONG = 'PR-4107256-8459273FA23C468A991CCA05B34AD9B7'

class LookupTests(unittest.TestCase):
    def request(self, payload, status=200):
        response = Mock(status=status)
        response.json.return_value = payload
        request = Mock()
        request.get.return_value = response
        return request, response

    def test_exact_coordinates_and_registration(self):
        request, response = self.request({'codeProperty': CORRECT})
        self.assertEqual(lookup_property(request, -23.266165, -53.290072).registration, CORRECT)
        self.assertEqual(request.get.call_args.kwargs['params'], {'lat': -23.266165, 'lng': -53.290072})
        response.dispose.assert_called_once()

    def test_bad_responses_fail_without_fallback(self):
        for payload, status in [(None, 200), (None, 204), ({}, 503), ({'codeProperty':'bad'},200), ([],200)]:
            with self.subTest(payload=payload, status=status):
                request, response = self.request(payload, status)
                with self.assertRaises(PortalError):
                    lookup_property(request, -23.266165, -53.290072)
                response.dispose.assert_called_once()

    def test_invalid_coordinates_make_no_request(self):
        for lat, lon in [(91,0),(0,181),(float('nan'),0)]:
            request = Mock()
            with self.assertRaises(PortalError):
                lookup_property(request,lat,lon)
            request.get.assert_not_called()

    def test_formatted_code_matches(self):
        self.assertEqual(verify_registration('PR-4107256-605F.9098.83AA.4304.9A3F.13A6.49F9.C99A',CORRECT),CORRECT)

    def test_different_property_is_rejected(self):
        with self.assertRaisesRegex(PortalError,'Property mismatch'):
            verify_registration(WRONG,CORRECT)

    def test_wrong_search_response_never_opens_details(self):
        page=Mock()
        page.locator.return_value.input_value.return_value=CORRECT
        response=Mock(status=200)
        response.json.return_value={'codeProperty':WRONG}
        pending=Mock(value=response)
        manager=Mock()
        manager.__enter__=Mock(return_value=pending)
        manager.__exit__=Mock(return_value=False)
        page.expect_response.return_value=manager
        with patch('src.portal.lookup_property',return_value=Property(CORRECT)):
            with self.assertRaisesRegex(PortalError,'Property mismatch'):
                open_property(page,-23.266165,-53.290072,progress=lambda *args:None)
        self.assertEqual(page.get_by_role.call_count,1)
        self.assertEqual(page.get_by_role.call_args.kwargs['name'],'Buscar')
        page.evaluate.assert_not_called()

    def test_wrong_visible_details_are_rejected_even_when_response_matches(self):
        page=Mock()
        page.locator.return_value.input_value.return_value=CORRECT
        page.locator.return_value.get_by_text.return_value.first.inner_text.return_value=WRONG
        response=Mock(status=200)
        response.json.return_value={'codeProperty':CORRECT}
        manager=Mock()
        manager.__enter__=Mock(return_value=Mock(value=response))
        manager.__exit__=Mock(return_value=False)
        page.expect_response.return_value=manager
        with patch('src.portal.lookup_property',return_value=Property(CORRECT)):
            with self.assertRaisesRegex(PortalError,'Property mismatch'):
                open_property(page,-23.266165,-53.290072,progress=lambda *args:None)
        self.assertEqual(page.get_by_role.call_count,1)

if __name__ == '__main__':
    unittest.main()
