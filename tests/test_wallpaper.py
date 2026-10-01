import base64
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import install
import theme_settings as settings


class WallpaperTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.terminal = self.root / 'terminal.json'
        self.runtime = self.root / 'runtime.json'
        self.state = self.root / 'install-state.json'
        self.original = {'defaultProfile': 'other', 'profiles': {'defaults': {'font': {'size': 15}},
            'list': [{'guid': 'other', 'name': 'My shell'}]}, 'actions': [{'id': 'keep-me'}]}
        self.terminal.write_text(json.dumps(self.original))
        self.palette = json.loads((install.ROOT / 'palette.json').read_text())
        text = install.terminal_config(self.terminal.read_text(), self.root, self.palette)
        install.apply_changes({self.terminal: text.encode(), self.runtime: json.dumps({
            'native': ['nonexistent-codex-test-sentinel'], 'terminal_settings': str(self.terminal),
            'wallpaper': False}).encode()}, self.state)
        (self.root / 'assets').mkdir()
        shutil.copy(install.ROOT / 'assets/b1scu1tk1d-landscape.png', self.root / 'assets')

    def test_on_off_status_persist_and_preserve_other_profiles(self):
        self.assertFalse(settings.set_wallpaper(self.root, 'status'))
        self.assertTrue(settings.set_wallpaper(self.root, 'on'))
        self.assertTrue(settings.set_wallpaper(self.root, 'status'))
        data = json.loads(self.terminal.read_text())
        self.assertEqual(data['profiles']['list'][0], self.original['profiles']['list'][0])
        self.assertEqual(data['defaultProfile'], 'other')
        self.assertEqual(data['actions'], self.original['actions'])
        self.assertEqual(data['profiles']['defaults'], self.original['profiles']['defaults'])
        profile = data['profiles']['list'][1]
        self.assertEqual(profile['name'], settings.TITLE)
        self.assertTrue(Path(profile['backgroundImage']).is_file())
        self.assertEqual(profile['backgroundImageOpacity'], .10)
        self.assertFalse(settings.set_wallpaper(self.root, 'off'))
        self.assertFalse(settings.set_wallpaper(self.root, 'status'))
        self.assertFalse(json.loads(self.runtime.read_text())['wallpaper'])

    def test_cli_toggle_exits_without_launching_codex_and_survives_restart(self):
        shutil.copy(install.ROOT / 'windows/cli.py', self.root)
        shutil.copy(install.ROOT / 'theme_settings.py', self.root)
        for mode, expected in [('on', 'on'), ('status', 'on'), ('off', 'off'), ('status', 'off')]:
            run = subprocess.run([sys.executable, str(self.root/'cli.py'), '--magik', '--wallpaper', mode],
                                 capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertIn('wallpaper: ' + expected, run.stdout)

    def test_invalid_control_does_not_consume_literal_prompt_text(self):
        self.assertIsNone(settings.wallpaper_action(['--magik', '--', '--wallpaper', 'on']))
        self.assertIsNone(settings.wallpaper_action(['exec', '--wallpaper', 'on']))
        self.assertEqual(settings.wallpaper_action(['--widowmaker', '--wallpaper', 'off']), 'off')
        with self.assertRaises(ValueError):
            settings.wallpaper_action(['--magik', '--wallpaper', 'on', '--yolo'])

    def test_uninstall_restores_originals_after_multiple_toggles(self):
        settings.set_wallpaper(self.root, 'on')
        settings.set_wallpaper(self.root, 'off')
        self.assertEqual(install.uninstall(self.state), 0)
        self.assertEqual(json.loads(self.terminal.read_text()), self.original)

    def test_toggle_does_not_hide_user_edits_from_uninstall(self):
        data = json.loads(self.terminal.read_text())
        data['custom-user-setting'] = 'preserve this'
        self.terminal.write_text(json.dumps(data))
        settings.set_wallpaper(self.root, 'on')
        self.assertEqual(install.uninstall(self.state), 2)
        self.assertEqual(json.loads(self.terminal.read_text())['custom-user-setting'], 'preserve this')

    def test_missing_asset_leaves_settings_unchanged(self):
        (self.root / 'assets/b1scu1tk1d-landscape.png').unlink()
        before = self.terminal.read_bytes()
        with self.assertRaises(ValueError):
            settings.set_wallpaper(self.root, 'on')
        self.assertEqual(before, self.terminal.read_bytes())

    def test_failed_toggle_rolls_back(self):
        paths = [self.terminal, self.runtime, self.state]
        before = {p: p.read_bytes() for p in paths}
        original = Path.write_bytes
        def fail(path, value):
            if path == self.runtime:
                raise OSError('Simulated locked runtime')
            return original(path, value)
        with patch.object(Path, 'write_bytes', fail):
            with self.assertRaises(OSError):
                settings.set_wallpaper(self.root, 'on')
        self.assertEqual(before, {p: p.read_bytes() for p in paths})

    def test_theme_text_contrast_with_brightest_possible_wallpaper(self):
        def rgb(h):
            return [int(h[i:i+2], 16) / 255 for i in (1, 3, 5)]
        def luminance(values):
            linear = [v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4 for v in values]
            return sum(v*w for v, w in zip(linear, (.2126, .7152, .0722)))
        opacity = settings.WALLPAPER_OPACITY
        background = [(1-opacity)*v+opacity for v in rgb(self.palette['ink'])]
        for color in ('cream', 'mute', 'amber', 'cyan', 'rose', 'green', 'blue', 'magenta'):
            ratio = (luminance(rgb(self.palette[color]))+.05)/(luminance(background)+.05)
            self.assertGreaterEqual(ratio, 4.5, color)

    def test_full_install_defaults_off_and_upgrade_preserves_toggle(self):
        home = self.root / 'fresh-home'
        codex_home = home / '.codex'
        native = self.root / 'codex.exe'
        native.write_bytes(b'not executed by installer')
        argv = ['install.py', '--terminal-settings', str(self.terminal), '--codex-executable', str(native)]
        with patch.object(install.sys, 'platform', 'win32'), patch.object(Path, 'home', return_value=home), \
             patch.dict(os.environ, {'CODEX_HOME': str(codex_home)}), \
             patch.object(install, 'update_user_path', return_value=False), patch.object(sys, 'argv', argv):
            self.assertEqual(install.main(), 0)
            installed = codex_home / 'magik-terminal'
            self.assertFalse(settings.set_wallpaper(installed, 'status'))
            self.assertTrue((codex_home / 'themes/widowmaker.tmTheme').exists())
            self.assertEqual((installed/'assets/b1scu1tk1d-landscape.png').read_bytes(),
                             (install.ROOT/'assets/b1scu1tk1d-landscape.png').read_bytes())
            settings.set_wallpaper(installed, 'on')
            self.assertEqual(install.main(), 0)
            self.assertTrue(settings.set_wallpaper(installed, 'status'))

    def test_wallpaper_is_independent_of_motion(self):
        data = json.loads(install.terminal_config(json.dumps(self.original), self.root,
                          self.palette, no_motion=True, wallpaper=True))
        profile = data['profiles']['list'][-1]
        self.assertIn('experimental.pixelShaderPath', profile)
        self.assertTrue(profile['backgroundImage'].endswith('.png'))


if __name__ == '__main__':
    unittest.main()
