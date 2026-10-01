"""Exercise the real PowerShell handoff with an argument-recording native stub."""
import base64
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


@unittest.skipUnless(sys.platform == 'win32', 'Windows PowerShell launcher')
class LaunchTests(unittest.TestCase):
    def launch(self, args):
        with tempfile.TemporaryDirectory(prefix='magik-launch-') as directory:
            root = Path(directory)
            shutil.copyfile(Path(__file__).resolve().parents[1] / 'windows/launch.ps1', root / 'launch.ps1')
            stub = root / 'native.py'
            stub.write_text('import json, pathlib, sys\npathlib.Path(__file__).with_suffix(".json").write_text(json.dumps(sys.argv[1:]))\n')
            (root / 'runtime.json').write_text(json.dumps({'native': [sys.executable, str(stub)]}))
            invocation = ['powershell.exe', '-NoProfile', '-File', str(root / 'launch.ps1')]
            if args is not None:
                invocation += ['-EncodedArguments', base64.b64encode(json.dumps(args).encode()).decode()]
            result = subprocess.run(invocation, capture_output=True, text=True, timeout=20)
            self.assertEqual(result.returncode, 0, result.stderr)
            return json.loads(stub.with_suffix('.json').read_text())

    def test_profile_menu_uses_shell_context(self):
        self.assertEqual(self.launch(None), ['--no-daemon'])

    def test_yolo_and_prompt_reach_native_intact(self):
        args = ['--dangerously-bypass-approvals-and-sandbox', 'prompt with spaces; $HOME & text']
        self.assertEqual(self.launch(args), ['--no-daemon'] + args)

    def test_prepared_payload_does_not_duplicate_flag(self):
        args = ['--no-daemon', '--dangerously-bypass-approvals-and-sandbox']
        self.assertEqual(self.launch(args), args)

    def test_remote_connections_stay_explicit(self):
        for args in [['--remote', 'ws://localhost:9000'], ['--remote=ws://localhost:9000']]:
            with self.subTest(args=args):
                self.assertEqual(self.launch(args), args)

    def test_literal_prompt_flags_do_not_select_remote(self):
        args = ['--', '--remote', '--no-daemon']
        self.assertEqual(self.launch(args), ['--no-daemon'] + args)


if __name__ == '__main__':
    unittest.main()
