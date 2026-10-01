"""Runs inside the separate Magik Ghostty instance; arguments remain arrays."""
import base64
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent


def main():
    runtime = json.loads((ROOT / 'runtime.json').read_text(encoding='utf-8'))
    args = json.loads(base64.b64decode(sys.argv[1]).decode()) if len(sys.argv) > 1 else []
    if not isinstance(args, list) or not all(isinstance(arg, str) for arg in args):
        raise ValueError('Invalid argument payload')
    env = os.environ.copy()
    env['MAGIK_PROFILE'] = str(ROOT)
    env['CODEX_HOME'] = runtime['codex_home']
    # LaunchServices need not inherit the invoking shell's PATH. Keep Node and
    # the native Codex entry reachable using the PATH captured at installation.
    env['PATH'] = runtime['path']
    invocation = runtime['native'] + args
    os.execvpe(invocation[0], invocation, env)


if __name__ == '__main__':
    main()
