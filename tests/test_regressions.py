"""Regression scenarios for client-reported failures and input boundaries."""
import io
import ssl
import tempfile
import unittest
import urllib.error
import zipfile
from pathlib import Path
from unittest.mock import Mock, patch
from playwright.sync_api import Error as PlaywrightError
from src.car_api import lookup_property, PortalError, Property
from src.coordinates import parse_coordinate
from src.downloads import download_zip
from src.portal import open_property

CAR = 'MS-5004304-D44BA71A5B55413EA855BF19B83D2EAF'
OTHER = 'MS-5004809-9544C3E81CE74B06941758DC66839B3C'

class CoordinateBoundaryTests(unittest.TestCase):
    pass

valid = [
 ('latitude_north_limit','90','latitude',90),
 ('latitude_south_limit','-90','latitude',-90),
 ('longitude_east_limit','180','longitude',180),
 ('longitude_west_limit','-180','longitude',-180),
 ('comma_decimal','-23,266165','latitude',-23.266165),
 ('southern_dms','23°15\'0"S','latitude',-23.25),
 ('western_dms','53°30\'0"W','longitude',-53.5),
 ('zero','0','latitude',0),
]
invalid = [
 ('empty','','latitude'), ('north_overflow','90.0001','latitude'),
 ('west_overflow','-180.001','longitude'), ('wrong_hemisphere','23W','latitude'),
 ('conflicting_sign','-23N','latitude'), ('minutes_overflow','23°60\'0"S','latitude'),
 ('seconds_overflow','23°0\'60"S','latitude'), ('nan','NaN','latitude'),
 ('infinity','inf','longitude'), ('invalid_axis','23','altitude'),
]
for name, value, axis, expected in valid:
 def check(self, value=value, axis=axis, expected=expected):
  self.assertAlmostEqual(parse_coordinate(value,axis), expected)
 setattr(CoordinateBoundaryTests,'test_'+name,check)
for name,value,axis in invalid:
 def check(self,value=value,axis=axis):
  with self.assertRaises(ValueError): parse_coordinate(value,axis)
 setattr(CoordinateBoundaryTests,'test_'+name,check)

class ApiRegressionTests(unittest.TestCase):
 def test_id_origin_preserved_with_registration(self):
  request=Mock(); response=request.get.return_value
  response.status=200; response.json.return_value={'codeProperty':CAR,'idOrigin':123}
  self.assertEqual(lookup_property(request,-23,-53),Property(CAR,123))
 def test_invalid_id_disables_download_identity(self):
  for origin in [True,-1,0,'123',None]:
   request=Mock(); response=request.get.return_value
   response.status=200; response.json.return_value={'codeProperty':CAR,'idOrigin':origin}
   with self.subTest(origin=origin): self.assertIsNone(lookup_property(request,-23,-53).id_origin)
 def test_network_failure_is_explicit(self):
  request=Mock(); request.get.side_effect=PlaywrightError('offline')
  with self.assertRaisesRegex(PortalError,'Coordinate lookup failed'): lookup_property(request,-23,-53)
 def test_invalid_json_disposes_response(self):
  request=Mock(); response=request.get.return_value
  response.status=200; response.json.side_effect=ValueError('bad JSON')
  with self.assertRaises(PortalError): lookup_property(request,-23,-53)
  response.dispose.assert_called_once()

class PortalRegressionTests(unittest.TestCase):
 def run_flow(self, after):
  page=Mock(); page.locator.return_value.input_value.return_value=CAR
  page.locator.return_value.get_by_text.return_value.first.inner_text.side_effect=[CAR,after]
  response=Mock(status=200); response.json.return_value={'codeProperty':CAR}
  manager=Mock(); manager.__enter__=Mock(return_value=Mock(value=response)); manager.__exit__=Mock(return_value=False)
  page.expect_response.return_value=manager
  selected=Mock()
  with patch('src.portal.lookup_property',return_value=Property(CAR,123)):
   if after != CAR:
    with self.assertRaisesRegex(PortalError,'Property mismatch'): open_property(page,-23,-53,progress=lambda *a:None,on_selected=selected)
    selected.assert_not_called()
   else:
    self.assertEqual(open_property(page,-23,-53,progress=lambda *a:None,on_selected=selected),CAR)
    selected.assert_called_once_with(Property(CAR,123))
 def test_client_ms_mismatch_after_click_is_blocked(self): self.run_flow(OTHER)
 def test_matching_details_release_download_identity(self): self.run_flow(CAR)

class DownloadFailureTests(unittest.TestCase):
 def check_failure(self, error):
  with tempfile.TemporaryDirectory() as folder:
   path=Path(folder)/'existing.zip'; path.write_bytes(b'existing')
   with patch('src.downloads.urllib.request.urlopen',side_effect=error) as request:
    with self.assertRaises(Exception): download_zip(123,path)
   self.assertEqual(path.read_bytes(),b'existing')
   self.assertEqual(list(Path(folder).iterdir()),[path])
   request.assert_called_once() # no automatic retry loop
 def test_certificate_error_no_insecure_retry(self):
  self.check_failure(urllib.error.URLError(ssl.SSLCertVerificationError('self-signed certificate in certificate chain')))
 def test_http_403_no_retry_loop(self): self.check_failure(urllib.error.HTTPError('https://example.invalid',403,'Forbidden',{},None))
 def test_http_500_preserves_file(self): self.check_failure(urllib.error.HTTPError('https://example.invalid',500,'Error',{},None))
 def test_timeout_preserves_file(self): self.check_failure(TimeoutError('timed out'))
 def test_empty_zip_is_rejected(self):
  data=io.BytesIO()
  with zipfile.ZipFile(data,'w'): pass
  response=io.BytesIO(data.getvalue()); response.status=200; response.headers={}
  with tempfile.TemporaryDirectory() as folder:
   with patch('src.downloads.urllib.request.urlopen',return_value=response):
    with self.assertRaises(RuntimeError): download_zip(123,Path(folder)/'empty.zip')
   self.assertEqual(list(Path(folder).iterdir()),[])
 def test_replace_permission_error_cleans_partial(self):
  data=io.BytesIO()
  with zipfile.ZipFile(data,'w') as z: z.writestr('data','content')
  response=io.BytesIO(data.getvalue()); response.status=200; response.headers={}
  with tempfile.TemporaryDirectory() as folder:
   path=Path(folder)/'existing.zip';path.write_bytes(b'existing')
   with patch('src.downloads.urllib.request.urlopen',return_value=response), patch('src.downloads.os.replace',side_effect=PermissionError('locked')):
    with self.assertRaises(PermissionError): download_zip(123,path)
   self.assertEqual(path.read_bytes(),b'existing')
   self.assertEqual(list(Path(folder).iterdir()),[path])
