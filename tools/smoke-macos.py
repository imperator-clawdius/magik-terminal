"""Real macOS isolated install + Ghostty validation + GUI command routing smoke.

Runs only against a temporary HOME and an inert native-Codex sentinel. No account,
model invocation, or real user configuration is involved.
"""
import base64
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile
import time

root = Path(__file__).resolve().parents[1]
if sys.platform != 'darwin':
    raise SystemExit('macOS only')
config_only = '--config-only' in sys.argv
if not config_only and os.environ.get('GITHUB_ACTIONS') == 'true':
    # Distinguish an unavailable hosted desktop from a failing Magik launcher.
    # Never skip an actual Ghostty failure after this system-app probe succeeds.
    try:
        subprocess.run(['/usr/bin/open', '-a', '/System/Applications/TextEdit.app'], check=True, timeout=15)
    except subprocess.TimeoutExpired:
        print('GUI UNAVAILABLE: even the macOS TextEdit launch timed out. '
              'Only config/direct-session coverage is available on this runner.', flush=True)
        raise SystemExit(77)
with tempfile.TemporaryDirectory(prefix='magik-ci-') as tmp:
    home = Path(tmp).resolve()
    env = os.environ.copy()
    env.update(HOME=str(home), CODEX_HOME=str(home / '.codex'))
    native = home / 'native-sentinel'
    result = home / 'result.json'
    hold = home / 'hold-open'
    if not config_only:
        # A Codex session stays open. Keep both inert sessions alive so this
        # checks simultaneous independent instances without racing AppKit quit.
        hold.touch()
    native.write_text('#!' + sys.executable + '\nimport json, os, sys, time\nfrom pathlib import Path\n'
                     + 'result = Path(' + repr(str(result)) + ')\n'
                     + 'pending = result.with_suffix(".pending")\n'
                     + 'pending.write_text(json.dumps({"args":sys.argv[1:],"profile":os.environ.get("MAGIK_PROFILE"),"pid":os.getpid()}))\n'
                     + 'pending.replace(result)\n'
                     + 'deadline = time.monotonic() + 60\n'
                     + 'while Path(' + repr(str(hold)) + ').exists() and time.monotonic() < deadline:\n    time.sleep(.1)\n')
    native.chmod(0o755)
    print('Installing isolated Mac instance...', flush=True)
    subprocess.run([sys.executable, str(root / 'macos/install.py'), '--codex-executable', str(native), '--wallpaper', 'on'], env=env, check=True, timeout=45)
    installed = home / '.codex/magik-terminal-macos'
    for args in [[], ['--dangerously-bypass-approvals-and-sandbox', 'literal; $HOME "quoted"']]:
        result.unlink(missing_ok=True)
        payload = base64.b64encode(json.dumps(args).encode()).decode()
        initial = shlex.join([sys.executable, str(installed / 'session.py'), payload])
        if config_only:
            print('Testing native session directly (no GUI): ' + repr(args), flush=True)
            subprocess.run([sys.executable, str(installed / 'session.py'), payload], check=True, timeout=15)
        else:
            print('Starting Ghostty with sentinel args: ' + repr(args), flush=True)
            try:
                subprocess.run(['/usr/bin/open', '-na', '/Applications/Ghostty.app', '--args',
                                '--config-default-files=false', '--config-file=' + str(installed / 'ghostty.conf'),
                                '--initial-command=' + initial], check=True, timeout=45)
            except subprocess.TimeoutExpired:
                sample = home / 'ghostty-sample.txt'
                subprocess.run(['/usr/bin/sample', 'ghostty', '1', '-file', str(sample)], timeout=10, check=False)
                if sample.exists():
                    print(sample.read_text(errors='replace')[:12000], flush=True)
                raise
            print('LaunchServices returned; waiting for sentinel...', flush=True)
        deadline = time.monotonic() + 30
        while not result.exists() and time.monotonic() < deadline:
            time.sleep(.25)
        if not result.exists():
            raise SystemExit('Ghostty GUI did not execute the isolated sentinel within 30 seconds.')
        data = json.loads(result.read_text())
        assert data['args'] == args, data
        assert data['profile'] == str(installed), data
        print(('Direct' if config_only else 'Ghostty GUI') + ' native session executed exact argv:', args, flush=True)
    print('Checking wallpaper command...', flush=True)
    hold.unlink(missing_ok=True)
    subprocess.run([str(home / '.local/bin/codex'), '--magik', '--wallpaper', 'off'], env=env, check=True, timeout=20)
    print('Uninstalling isolated instance...', flush=True)
    subprocess.run([sys.executable, str(root / 'macos/install.py'), '--uninstall'], env=env, check=True, timeout=20)
print('Real macOS install, Ghostty validation, ' + ('direct sessions' if config_only else 'separate-instance GUI launches') + ', toggle, and uninstall passed.')
