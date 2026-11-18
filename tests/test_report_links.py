import unittest
from unittest.mock import patch

from src.report_links import open_statement, statement_url

CAR = "PR-4107256-605F909883AA43049A3F13A649F9C99A"


class ReportTests(unittest.TestCase):
    def test_url_uses_selected_registration(self):
        self.assertEqual(statement_url(CAR.lower()), "https://www.car.gov.br/#/consultar/" + CAR)

    def test_opens_statement_in_default_browser(self):
        with patch("src.report_links.webbrowser.open", return_value=True) as launch:
            open_statement(CAR)
        launch.assert_called_once_with(statement_url(CAR), new=1)

    def test_missing_default_browser_raises_error(self):
        with patch("src.report_links.webbrowser.open", return_value=False):
            with self.assertRaisesRegex(OSError, "default web browser"):
                open_statement(CAR)

    def test_invalid_registration_does_not_launch(self):
        with patch("src.report_links.webbrowser.open") as launch:
            with self.assertRaises(RuntimeError):
                open_statement("invalid/other-page")
        launch.assert_not_called()
