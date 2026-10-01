"""Transparent Codex command wrapper; Magik runs in the current terminal."""
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
TITLE = 'Magik Terminal for Codex (By W1d0wm4k3r)'
BATCH = {'exec', 'e', 'review', 'login', 'logout', 'mcp', 'mcp-server', 'plugin',
         'app-server', 'remote-control', 'app', 'completion', 'update', 'doctor',
         'sandbox', 'debug', 'apply', 'a', 'queue', 'archive', 'delete',
         'migrate-rollouts', 'unarchive', 'cloud', 'exec-server', 'features', 'help'}


def parse_args(args):
    # -- terminates our flag parsing too, so literal prompt text is untouched.
    split = args.index('--') if '--' in args else len(args)
    flags, tail = args[:split], args[split:]
    magik = any(arg in ('--magik', '--widowmaker') for arg in flags)
    flags = [arg for arg in flags if arg not in ('--magik', '--widowmaker')]
    if magik:
        flags = ['--dangerously-bypass-approvals-and-sandbox' if arg == '--yolo' else arg for arg in flags]
    return magik, flags + tail


def command(args, native, *, interactive=True):
    magik, forwarded = parse_args(args)
    batch = not interactive or any(x in BATCH or x in {'-h', '--help', '-V', '--version'} for x in forwarded)
    if not magik or batch:
        return native + forwarded
    # The shared daemon may have been started by a non-admin desktop session.
    # Keep local interactive Magik sessions in their launching shell's context.
    flags = forwarded[:forwarded.index('--')] if '--' in forwarded else forwarded
    if '--no-daemon' not in flags and not any(x == '--remote' or x.startswith('--remote=') for x in flags):
        forwarded = ['--no-daemon'] + forwarded
    # Inherit the launching console, working directory, and streams. Terminal
    # appearance belongs to the host profile, not to a newly spawned tab.
    return native + forwarded


def main():
    from theme_settings import wallpaper_action, set_wallpaper
    try:
        mode = wallpaper_action(sys.argv[1:])
        if mode:
            enabled = set_wallpaper(ROOT, mode)
            print(TITLE + ' wallpaper: ' + ('on' if enabled else 'off') + '. Saved for future launches.')
            return 0
    except (ValueError, KeyError, OSError) as error:
        print(f'Wallpaper settings failed: {error}', file=sys.stderr)
        return 1
    config = json.loads((ROOT / 'runtime.json').read_text(encoding='utf-8'))
    invocation = command(sys.argv[1:], config['native'],
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
        print(f'Magik Terminal could not launch Codex: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
