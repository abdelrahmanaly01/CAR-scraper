"""Lifecycle tests; do not open a browser or contact the portal."""
import tkinter as tk
import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch
from src.car_gui import CarApp


class GuiTests(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.temp = tempfile.TemporaryDirectory()
        self.preferences = Path(self.temp.name) / 'preferences.json'
        self.app = CarApp(self.root, settings_path=self.preferences)
        self.root.withdraw()

    def test_default_preferences_use_project_config(self):
        root = tk.Tk()
        root.withdraw()
        app = CarApp(root)
        try:
            expected = Path(__file__).resolve().parent.parent / 'config' / 'preferences.json'
            self.assertEqual(app.settings_path, expected)
        finally:
            app.close()

    def tearDown(self):
        if not self.app.closing:
            self.app.close()
        self.temp.cleanup()

    def test_invalid_input_never_starts_worker(self):
        self.app.latitude.set('91')
        self.app.longitude.set('0')
        with patch('src.car_gui.subprocess.Popen') as launch:
            self.app.start()
            launch.assert_not_called()
        self.assertFalse(self.app.busy)
        self.assertTrue(self.app.error.cget('text'))

    def test_worker_launches_from_project_root_as_module(self):
        self.app.latitude.set('0')
        self.app.longitude.set('0')
        with patch('src.car_gui.subprocess.Popen', return_value=object()) as launch, \
                patch('src.car_gui.threading.Thread') as thread:
            self.app.start()
        command = launch.call_args.args[0]
        self.assertEqual(command[1:4], ['-u', '-m', 'src.candidate_worker'])
        self.assertEqual(launch.call_args.kwargs['cwd'],
                         Path(__file__).resolve().parent.parent)
        thread.assert_called_once()
        self.app.process = None

    def test_closed_browser_yes_restores_form(self):
        self.app.busy = self.app.ready = True
        self.app.set_inputs(False)
        with patch.object(self.app, 'ask_again', return_value=True) as prompt:
            self.app.finished(0)
            prompt.assert_called_once()
        self.assertFalse(self.app.busy)
        self.assertEqual(str(self.app.start_button.cget('state')), 'normal')
        self.assertFalse(self.app.closing)

    def test_closed_browser_no_exits(self):
        self.app.ready = True
        with patch.object(self.app, 'ask_again', return_value=False):
            self.app.finished(0)
        self.assertTrue(self.app.closing)

    def test_cancel_returns_without_session_question(self):
        self.app.cancelled = self.app.busy = True
        with patch.object(self.app, 'ask_again') as prompt:
            self.app.finished(1)
            prompt.assert_not_called()
        self.assertFalse(self.app.busy)
        self.assertIn('cancelled', self.app.status.cget('text'))

    def test_failure_allows_retry(self):
        self.app.busy = True
        self.app.failure = 'Portal unavailable'
        with patch.object(self.app, 'dialog') as error:
            self.app.finished(1)
            error.assert_called_once()
        self.assertFalse(self.app.busy)
        self.assertEqual(str(self.app.start_button.cget('state')), 'normal')

    def test_switch_during_loading_preserves_input_and_state(self):
        self.app.fill_sample()
        self.app.busy = True
        self.app.set_inputs(False)
        self.app.update_stage('map', 'Loading the map...')
        self.app.language_choice.set('Português (Brasil)')
        self.app.change_language()
        self.assertEqual(self.app.start_button.cget('text'), 'Buscar imóvel')
        self.assertIn('Carregando', self.app.status.cget('text'))
        self.assertEqual(str(self.app.start_button.cget('state')), 'disabled')
        self.assertEqual(self.app.latitude.get(), '-8.2652558333')
        self.assertEqual(self.app.tr('no'), 'Não, sair')
        self.app.language_choice.set('English')
        self.app.change_language()
        self.assertIn('Loading', self.app.status.cget('text'))

    def test_preference_restored_and_errors_localized(self):
        self.app.language_choice.set('Português (Brasil)')
        self.app.change_language()
        self.app.close()
        self.root = tk.Tk()
        self.root.withdraw()
        self.app = CarApp(self.root, settings_path=self.preferences)
        self.root.withdraw()
        self.assertEqual(self.app.language, 'pt-BR')
        self.app.latitude.set('invalid')
        self.app.start()
        self.assertIn('Coordenadas inválidas', self.app.error.cget('text'))

    def test_translation_keys_match(self):
        from src.translations import TEXT
        self.assertEqual(set(TEXT['en']), set(TEXT['pt-BR']))

    def test_small_window_can_scroll_to_bottom(self):
        self.root.state('normal')
        self.root.geometry('440x320')
        self.root.update()
        self.app.canvas.yview_moveto(1)
        self.root.update()
        top, bottom = self.app.canvas.yview()
        self.assertGreater(top, 0)
        self.assertAlmostEqual(bottom, 1.0, places=2)

    def test_selecting_candidate_controls_download_identity(self):
        self.app.candidates = [
            {'registration': 'PR-4107256-605F909883AA43049A3F13A649F9C99A', 'id_origin': 5114292, 'inside': True, 'distance_m': 297, 'area': 925},
            {'registration': 'PR-4107256-861EC295E2A34AFD81F78DF64948C8DC', 'id_origin': 1383498, 'inside': False, 'distance_m': 333, 'area': 500},
        ]
        self.app.candidate_choice.configure(values=[x['registration'] for x in self.app.candidates], state='readonly')
        self.app.candidate_choice.current(1)
        self.app.select_candidate()
        self.assertEqual(self.app.id_origin, 1383498)
        self.assertIn('outside', self.app.candidate_details.cget('text'))
        self.app.candidate_choice.current(0)
        self.app.select_candidate()
        self.assertEqual(self.app.id_origin, 5114292)
        self.assertIn('inside', self.app.candidate_details.cget('text'))

    def test_statement_only_opens_verified_session_registration(self):
        car = 'PR-4107256-605F909883AA43049A3F13A649F9C99A'
        with patch('src.car_gui.open_statement') as launch:
            self.app.open_report()
            launch.assert_not_called()
            self.app.events.put((self.app.session_id, {'event': 'ready', 'registration': car}))
            self.app.poll()
            self.app.open_report()
            launch.assert_called_once_with(car)
        self.app.cancelled = True
        self.app.finished(0)
        self.assertIsNone(self.app.registration)
        self.assertEqual(str(self.app.report_button.cget('state')), 'disabled')


if __name__ == '__main__':
    unittest.main()
