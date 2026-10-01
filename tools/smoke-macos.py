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
with tempfile.TemporaryDirectory(prefix='magik-ci-') as tmp:
    home = Path(tmp)
    env = os.environ.copy()
    env.update(HOME=tmp, CODEX_HOME=str(home / '.codex'))
    native = home / 'native-sentinel'
    result = home / 'result.json'
    native.write_text('#!' + sys.executable + '\nimport json, os, sys\nfrom pathlib import Path\n'
                     + 'Path(' + repr(str(result)) + ').write_text(json.dumps({"args":sys.argv[1:],"profile":os.environ.get("MAGIK_PROFILE")}))\n')
    native.chmod(0o755)
    subprocess.run([sys.executable, str(root / 'macos/install.py'), '--codex-executable', str(native), '--wallpaper', 'on'], env=env, check=True)
    installed = home / '.codex/magik-terminal-macos'
    for args in [[], ['--dangerously-bypass-approvals-and-sandbox', 'literal; $HOME "quoted"']]:
        result.unlink(missing_ok=True)
        payload = base64.b64encode(json.dumps(args).encode()).decode()
        initial = shlex.join([sys.executable, str(installed / 'session.py'), payload])
        subprocess.run(['/usr/bin/open', '-na', '/Applications/Ghostty.app', '--args',
                        '--config-default-files=false', '--config-file=' + str(installed / 'ghostty.conf'),
                        '--initial-command=' + initial], check=True)
        deadline = time.monotonic() + 30
        while not result.exists() and time.monotonic() < deadline:
            time.sleep(.25)
        if not result.exists():
            raise SystemExit('Ghostty GUI did not execute the isolated sentinel within 30 seconds.')
        data = json.loads(result.read_text())
        assert data['args'] == args, data
        assert data['profile'] == str(installed), data
        print('Ghostty native session executed exact argv:', args)
    subprocess.run([str(home / '.local/bin/codex'), '--magik', '--wallpaper', 'off'], env=env, check=True)
    subprocess.run([sys.executable, str(root / 'macos/install.py'), '--uninstall'], env=env, check=True)
print('Real macOS install, Ghostty validation, separate-instance launches, toggle, and uninstall passed.')
