import base64
import json
from pathlib import Path
import plistlib
import tempfile
import tomllib
import unittest
from unittest.mock import patch
import install


class InstallerTests(unittest.TestCase):
    def test_preserves_codex_settings_and_tables(self):
        original = '# user comment\nmodel="example"\n[tui]\nnotifications=false\n[tui.other]\nx=1\n[projects."C:/work"]\ntrust_level="trusted"\n'
        result = install.theme_config(original)
        self.assertIn('# user comment', result)
        self.assertEqual(tomllib.loads(result)['tui'], {'theme': 'magik', 'notifications': False, 'other': {'x': 1}})
        self.assertEqual(install.theme_config(result), result)

    def test_adds_or_replaces_theme(self):
        for text in ['', 'model="example"\n', '[tui]\ntheme="old"\n']:
            self.assertEqual(tomllib.loads(install.theme_config(text))['tui']['theme'], 'magik')

    def test_rejects_inline_table_without_writing(self):
        with self.assertRaises(ValueError):
            install.theme_config('tui = { theme = "old" }\n')

    def test_jsonc_preserves_strings(self):
        text = '{/* hi */"url":"https://site.test/a//b", "literal":",}","items":[1, // comment\n],}'
        self.assertEqual(install.jsonc(text), {'url': 'https://site.test/a//b', 'literal': ',}', 'items': [1]})

    def test_terminal_settings_survive_repeat_install(self):
        palette = json.loads((install.ROOT / 'palette.json').read_text())
        original = json.dumps({'defaultProfile': 'mine', 'profiles': {'defaults': {'font': {'size': 16}}, 'list': [{'guid': 'mine', 'name': 'My shell'}]}, 'actions': [1]})
        once = install.terminal_config(original, Path('C:/Magik'), palette)
        twice = install.terminal_config(once, Path('C:/Magik'), palette)
        self.assertEqual(once, twice)
        data = json.loads(twice)
        self.assertEqual(data['defaultProfile'], 'mine')
        self.assertEqual(data['actions'], [1])
        self.assertEqual(data['profiles']['defaults']['font']['size'], 16)
        still = json.loads(install.terminal_config(twice, Path('C:/Magik'), palette, True))
        self.assertNotIn('experimental.pixelShaderPath', still['profiles']['list'][-1])

    def test_theme_is_valid_plist(self):
        palette = json.loads((install.ROOT / 'palette.json').read_text())
        theme = plistlib.loads(install.theme_bytes(palette))
        self.assertEqual(theme['settings'][0]['settings']['foreground'], '#f2efe6')

    def test_profile_block_is_idempotent(self):
        original = 'function prompt { "custom> " }\n'
        once = install.managed_block(original, 'example')
        self.assertEqual(once, install.managed_block(once, 'example'))
        self.assertIn(original, once)

    def test_install_uninstall_restores_exact_original_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            old, new, state = root/'old', root/'new', root/'state.json'
            original = b'\xff\xfe#\x00 \x00u\x00\r\x00\n\x00'
            old.write_bytes(original)
            install.apply_changes({old: b'changed', new: b'new'}, state)
            install.apply_changes({old: b'changed again', new: b'new'}, state)
            self.assertEqual(install.uninstall(state), 0)
            self.assertEqual(old.read_bytes(), original)
            self.assertFalse(new.exists())

    def test_uninstall_retains_later_user_edits_and_backup(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            file, state = root/'file', root/'state.json'
            file.write_bytes(b'original')
            install.apply_changes({file: b'installed'}, state)
            file.write_bytes(b'user edited')
            self.assertEqual(install.uninstall(state), 2)
            self.assertEqual(file.read_bytes(), b'user edited')
            self.assertEqual(base64.b64decode(json.loads(state.read_text())['files'][str(file)]['before']), b'original')

    def test_failed_install_rolls_back(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            file, state = root/'file', root/'state.json'
            file.write_bytes(b'original')
            write = Path.write_bytes
            def fail(path, value):
                if value == b'fail':
                    raise OSError('test failure')
                return write(path, value)
            with patch.object(Path, 'write_bytes', fail):
                with self.assertRaises(OSError):
                    install.apply_changes({file: b'fail'}, state)
            self.assertEqual(file.read_bytes(), b'original')
            self.assertFalse(state.exists())


if __name__ == '__main__':
    unittest.main()
