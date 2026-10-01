import base64
import importlib.util
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import install
from macos import install as mac_install
from macos.settings import ghostty_config

spec = importlib.util.spec_from_file_location('windows_cli', install.ROOT / 'windows/cli.py')
windows_cli = importlib.util.module_from_spec(spec)
spec.loader.exec_module(windows_cli)
with patch.dict(sys.modules, {'windows_cli': windows_cli}):
    from macos import cli


class MacTests(unittest.TestCase):
    def runtime(self, root):
        return dict(native=['/usr/local/bin/codex'], python='/opt/Python Folder/python3',
                    ghostty_app='/Applications/Ghostty.app', wallpaper=False, no_motion=False,
                    shader='magik-test.glsl', palette=json.loads((install.ROOT / 'palette.json').read_text()))

    def test_separate_instance_has_lossless_explicit_yolo(self):
        root = Path('/Users/A Name/.codex/magik-terminal-macos')
        runtime = self.runtime(root)
        for args in [[], ['--yolo', 'café "quoted"; $(touch bad)']]:
            cmd = cli.command(['--magik'] + args, runtime, root=root, cwd='/Work Space')
            self.assertEqual(cmd[:4], ['/usr/bin/open', '-na', runtime['ghostty_app'], '--args'])
            self.assertIn('--config-default-files=false', cmd)
            self.assertIn('--working-directory=/Work Space', cmd)
            payload_cmd = shlex.split(next(x.split('=', 1)[1] for x in cmd if x.startswith('--initial-command=')))
            self.assertEqual(payload_cmd[:2], [runtime['python'], str(root / 'session.py')])
            expected = ['--dangerously-bypass-approvals-and-sandbox', args[1]] if args else []
            self.assertEqual(json.loads(base64.b64decode(payload_cmd[2])), expected)

    def test_passthrough_and_existing_instance(self):
        runtime = self.runtime(Path('/tmp/magik'))
        for args, kwargs in [(['exec', '--json', 'hi'], {}), (['--magik', '--version'], {}),
                             (['--magik'], {'interactive': False}), (['--magik'], {'in_profile': True})]:
            result = cli.command(args, runtime, **kwargs)
            self.assertEqual(result[0], runtime['native'][0])
        self.assertEqual(cli.command(['--magik', '--yolo'], runtime, in_profile=True),
                         runtime['native'] + ['--dangerously-bypass-approvals-and-sandbox'])

    def test_config_quotes_paths_and_keeps_native_graphics(self):
        runtime = self.runtime(Path('/tmp/Magik Folder'))
        runtime['wallpaper'] = True
        text = ghostty_config(Path('/tmp/Magik Folder'), runtime)
        self.assertIn('background-image-opacity = 0.10', text)
        image_value = next(line.split(' = ', 1)[1] for line in text.splitlines() if line.startswith('background-image = '))
        self.assertEqual(json.loads(image_value), str(Path('/tmp/Magik Folder/assets/b1scu1tk1d-landscape.png')))
        self.assertIn('window-save-state = never', text)
        self.assertNotIn('allow_remote_control', text)

    def test_isolated_install_toggle_upgrade_and_uninstall(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp).resolve() / 'Home Space'
            home.mkdir()
            codex_home = home / '.codex'
            ghostty = home / 'Ghostty.app'
            binary = ghostty / 'Contents/MacOS/ghostty'
            binary.parent.mkdir(parents=True)
            binary.touch()
            native = home / 'native-codex'
            native.write_text('#!/bin/sh\nprintf "%s\\n" "$@"\nexit 23\n', encoding='utf-8', newline='\n')
            native.chmod(0o755)
            zshrc = home / '.zshrc'
            zshrc.write_text('# keep my shell\n')
            argv = ['install.py', '--ghostty-app', str(ghostty), '--codex-executable', str(native)]
            with patch.object(mac_install.sys, 'platform', 'darwin'), patch.object(Path, 'home', return_value=home), \
                 patch.dict(os.environ, {'CODEX_HOME': str(codex_home)}), patch.object(sys, 'argv', argv), \
                 patch.object(mac_install.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, '', '')):
                self.assertEqual(mac_install.main(), 0)
            root = codex_home / 'magik-terminal-macos'
            modules = {'install_support': install, 'macos_settings': sys.modules['macos.settings']}
            with patch.dict(sys.modules, modules):
                self.assertTrue(cli.wallpaper(root, 'on'))
                self.assertTrue(cli.wallpaper(root, 'status'))
            with patch.object(mac_install.sys, 'platform', 'darwin'), patch.object(Path, 'home', return_value=home), \
                 patch.dict(os.environ, {'CODEX_HOME': str(codex_home)}), patch.object(sys, 'argv', argv), \
                 patch.object(mac_install.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, '', '')):
                self.assertEqual(mac_install.main(), 0)
            self.assertTrue(json.loads((root / 'runtime.json').read_text())['wallpaper'])
            self.assertEqual(zshrc.read_text().count(install.START), 1)
            if os.name != 'nt':
                run = subprocess.run([str(home / '.local/bin/codex'), 'exec', 'literal; $HOME'], capture_output=True, text=True)
                self.assertEqual(run.returncode, 23)
                self.assertEqual(run.stdout.splitlines(), ['exec', 'literal; $HOME'])
            # Fresh-process wallpaper control must not run the native sentinel.
            run = subprocess.run([sys.executable, str(root / 'cli.py'), '--magik', '--wallpaper', 'off'], capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertIn('wallpaper: off', run.stdout)
            self.assertEqual(install.uninstall(root / 'install-state.json'), 0)
            self.assertEqual(zshrc.read_text(), '# keep my shell\n')


if __name__ == '__main__':
    unittest.main()
