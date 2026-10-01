import base64
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

spec = importlib.util.spec_from_file_location('magik_cli', Path(__file__).resolve().parents[1] / 'windows/cli.py')
cli = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cli)


class CommandTests(unittest.TestCase):
    def test_plain_codex_passes_through(self):
        args = ['exec', '--json', 'keep "quotes" and ; $variables']
        self.assertEqual(cli.command(args, ['codex.exe']), ['codex.exe'] + args)

    def test_magik_opens_themed_window_from_legacy_or_other_profiles(self):
        for profile_id in ['', 'ordinary-profile']:
            cmd = cli.command(['--magik'], ['codex.exe'], profile_id=profile_id, cwd='C:/Work Space')
            self.assertEqual(cmd[:8], ['wt.exe', '-w', 'new', 'new-tab', '-p', cli.GUID, '-d', 'C:/Work Space'])
            self.assertEqual(json.loads(base64.b64decode(cmd[-1])), ['--no-daemon'])

    def test_existing_magik_tab_is_reused(self):
        self.assertEqual(cli.command(['--magik'], ['codex.exe'], profile_id=cli.GUID.upper()),
                         ['codex.exe', '--no-daemon'])

    def test_yolo_is_explicit_and_arguments_are_lossless(self):
        prompt = 'Unicode café; "quotes" $PATH & other text'
        cmd = cli.command(['--magik', '--yolo', prompt], ['codex.exe'])
        self.assertEqual(json.loads(base64.b64decode(cmd[-1])), ['--no-daemon', '--dangerously-bypass-approvals-and-sandbox', prompt])

    def test_native_runtime_prefix_and_resume_are_preserved(self):
        native = ['C:/Program Files/nodejs/node.exe', 'C:/Codex/bin/codex.js']
        self.assertEqual(cli.command(['--magik', 'resume', '--last'], native, profile_id=cli.GUID),
                         native + ['--no-daemon', 'resume', '--last'])

    def test_explicit_remote_connection_is_preserved(self):
        for args in [['--remote', 'ws://localhost:9000'], ['--remote=ws://localhost:9000']]:
            cmd = cli.command(['--magik'] + args, ['codex.exe'])
            self.assertEqual(json.loads(base64.b64decode(cmd[-1])), args)

    def test_no_daemon_is_not_duplicated(self):
        cmd = cli.command(['--magik', '--no-daemon'], ['codex.exe'])
        self.assertEqual(json.loads(base64.b64decode(cmd[-1])), ['--no-daemon'])

    def test_literal_flags_do_not_change_daemon_selection(self):
        args = ['--', '--remote', '--no-daemon']
        cmd = cli.command(['--magik'] + args, ['codex.exe'])
        self.assertEqual(json.loads(base64.b64decode(cmd[-1])), ['--no-daemon'] + args)

    def test_automation_and_redirected_streams_never_spawn_window(self):
        for args in [['--magik', '--version'], ['--magik', 'exec', '--json', 'hi']]:
            self.assertEqual(cli.command(args, ['codex.exe'])[0], 'codex.exe')
        self.assertEqual(cli.command(['--magik'], ['codex.exe'], interactive=False), ['codex.exe'])

    def test_double_dash_preserves_literal_prompt_flags(self):
        self.assertEqual(cli.parse_args(['--magik', '--', '--yolo', '--magik']), (True, ['--', '--yolo', '--magik']))

    def test_widowmaker_alias_keeps_yolo_explicit(self):
        self.assertEqual(cli.parse_args(['--widowmaker']), (True, []))
        self.assertEqual(cli.parse_args(['--widowmaker', '--yolo']),
                         (True, ['--dangerously-bypass-approvals-and-sandbox']))


class ProcessTests(unittest.TestCase):
    def run_launcher(self, waits, profile_id=cli.GUID):
        with tempfile.TemporaryDirectory(prefix='magik-cli-') as directory:
            root = Path(directory)
            (root / 'runtime.json').write_text(json.dumps({'native': ['codex.exe']}))
            child = Mock()
            child.wait.side_effect = waits
            with patch.object(cli, 'ROOT', root), \
                 patch.object(cli.sys, 'argv', ['codex', '--magik', 'resume', '--last']), \
                 patch.object(cli.sys.stdin, 'isatty', return_value=True), \
                 patch.object(cli.sys.stdout, 'isatty', return_value=True), \
                 patch.dict(cli.os.environ, {'WT_PROFILE_ID': profile_id}), \
                 patch.object(cli.subprocess, 'Popen', return_value=child) as spawn:
                result = cli.main()
            # No shell, detached console, stream redirection, cwd, or env override.
            expected = cli.command(['--magik', 'resume', '--last'], ['codex.exe'], profile_id=profile_id, root=root)
            spawn.assert_called_once_with(expected)
            return result, child.wait.call_count

    def test_launch_inherits_console_and_returns_native_exit_code(self):
        self.assertEqual(self.run_launcher([23]), (23, 1))

    def test_ctrl_c_waits_for_attached_child(self):
        self.assertEqual(self.run_launcher([KeyboardInterrupt(), 130]), (130, 2))

    def test_missing_profile_id_hands_off_without_appearance_error(self):
        self.assertEqual(self.run_launcher([0], profile_id=''), (0, 1))


if __name__ == '__main__':
    unittest.main()
