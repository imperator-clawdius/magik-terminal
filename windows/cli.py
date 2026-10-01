"""Transparent Codex command wrapper; --magik opts into the terminal profile."""
import base64
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
GUID = '{89a85927-87d9-4b07-922a-3fc6a9f2dc61}'
BATCH = {'exec', 'e', 'review', 'login', 'logout', 'mcp', 'mcp-server', 'plugin',
         'app-server', 'remote-control', 'app', 'completion', 'update', 'doctor',
         'sandbox', 'debug', 'apply', 'a', 'queue', 'archive', 'delete',
         'migrate-rollouts', 'unarchive', 'cloud', 'exec-server', 'features', 'help'}


def parse_args(args):
    # -- terminates our flag parsing too, so literal prompt text is untouched.
    split = args.index('--') if '--' in args else len(args)
    flags, tail = args[:split], args[split:]
    magik = '--magik' in flags
    flags = [arg for arg in flags if arg != '--magik']
    if magik:
        flags = ['--dangerously-bypass-approvals-and-sandbox' if arg == '--yolo' else arg for arg in flags]
    return magik, flags + tail


def command(args, native, *, profile_id='', interactive=True, cwd=None, root=ROOT):
    magik, forwarded = parse_args(args)
    batch = not interactive or any(x in BATCH or x in {'-h', '--help', '-V', '--version'} for x in forwarded)
    if not magik or batch or profile_id.lower() == GUID:
        return native + forwarded
    payload = base64.b64encode(json.dumps(forwarded, ensure_ascii=False).encode()).decode()
    return ['wt.exe', '-w', '0', 'new-tab', '-p', 'Magik Terminal', '-d', cwd or os.getcwd(),
            'powershell.exe', '-NoLogo', '-NoExit', '-File', str(root / 'launch.ps1'),
            '-EncodedArguments', payload]


def main():
    config = json.loads((ROOT / 'runtime.json').read_text(encoding='utf-8'))
    invocation = command(sys.argv[1:], config['native'],
        profile_id=os.environ.get('WT_PROFILE_ID', ''),
        interactive=sys.stdin.isatty() and sys.stdout.isatty())
    try:
        child = subprocess.Popen(invocation)
        # The child receives the same console Ctrl+C. Keep waiting so the
        # wrapper doesn't leave an interactive child orphaned in the shell.
        while True:
            try:
                return child.wait()
            except KeyboardInterrupt:
                continue
    except OSError as error:
        print(f'Magik could not launch Codex: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
