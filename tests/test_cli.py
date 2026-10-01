import base64
import importlib.util
import json
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('magik_cli', Path(__file__).resolve().parents[1] / 'windows/cli.py')
cli = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cli)


class CommandTests(unittest.TestCase):
    def test_plain_codex_passes_through(self):
        args = ['exec', '--json', 'keep "quotes" and ; $variables']
        self.assertEqual(cli.command(args, ['codex.exe']), ['codex.exe'] + args)

    def test_magik_opens_profile_without_yolo(self):
        cmd = cli.command(['--magik'], ['codex.exe'], cwd='C:/Work Space')
        self.assertEqual(cmd[0], 'wt.exe')
        self.assertIn('Magik Terminal', cmd)
        self.assertIn('C:/Work Space', cmd)
        self.assertEqual(json.loads(base64.b64decode(cmd[-1])), [])

    def test_yolo_is_explicit_and_payload_is_lossless(self):
        prompt = 'Unicode café; "quotes" $PATH & other text'
        cmd = cli.command(['--magik', '--yolo', prompt], ['codex.exe'])
        self.assertEqual(json.loads(base64.b64decode(cmd[-1])), ['--dangerously-bypass-approvals-and-sandbox', prompt])

    def test_inside_magik_does_not_spawn_nested_tab(self):
        self.assertEqual(cli.command(['--magik', '--yolo'], ['codex.exe'], profile_id=cli.GUID),
                         ['codex.exe', '--dangerously-bypass-approvals-and-sandbox'])

    def test_automation_and_redirected_streams_never_spawn_window(self):
        for args in [['--magik', '--version'], ['--magik', 'exec', '--json', 'hi']]:
            self.assertEqual(cli.command(args, ['codex.exe'])[0], 'codex.exe')
        self.assertEqual(cli.command(['--magik'], ['codex.exe'], interactive=False), ['codex.exe'])

    def test_double_dash_preserves_literal_prompt_flags(self):
        self.assertEqual(cli.parse_args(['--magik', '--', '--yolo', '--magik']), (True, ['--', '--yolo', '--magik']))


if __name__ == '__main__':
    unittest.main()
