import unittest
from unittest.mock import patch

from src.report_links import open_statement, statement_url

CAR = "PR-4107256-605F909883AA43049A3F13A649F9C99A"


class ReportTests(unittest.TestCase):
    def test_url_uses_selected_registration(self):
        self.assertEqual(statement_url(CAR.lower()), "https://www.car.gov.br/#/consultar/" + CAR)

    def test_normal_chrome_has_no_automation_or_profile_flags(self):
        with patch("src.report_links.shutil.which", return_value="chrome.exe"), \
                patch("src.report_links.Path.is_file", return_value=True), \
                patch("src.report_links.subprocess.Popen") as launch:
            open_statement(CAR)
        launch.assert_called_once_with(["chrome.exe", "--new-window", statement_url(CAR)])

    def test_invalid_registration_does_not_launch(self):
        with patch("src.report_links.subprocess.Popen") as launch:
            with self.assertRaises(RuntimeError):
                open_statement("invalid/other-page")
        launch.assert_not_called()
