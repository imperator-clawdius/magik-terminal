"""macOS command wrapper. An isolated Ghostty instance carries Magik visuals."""
import base64
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys

from theme_settings import TITLE, wallpaper_action
from windows_cli import parse_args, BATCH

ROOT = Path(__file__).resolve().parent


def command(args, runtime, *, interactive=True, in_profile=False, cwd=None, root=ROOT):
    themed, forwarded = parse_args(args)
    batch = not interactive or any(x in BATCH or x in {'-h', '--help', '-V', '--version'} for x in forwarded)
    if not themed or batch or in_profile:
        return runtime['native'] + forwarded
    payload = base64.b64encode(json.dumps(forwarded, ensure_ascii=False).encode()).decode()
    # Pass one quoted command as a config option. No prompt text reaches a shell.
    # This also avoids older AppKit -e positional-argument/file-opening bugs.
    initial = shlex.join([runtime['python'], str(root / 'session.py'), payload])
    return ['/usr/bin/open', '-na', runtime['ghostty_app'], '--args',
            '--config-default-files=false', '--config-file=' + str(root / 'ghostty.conf'),
            '--working-directory=' + (cwd or os.getcwd()), '--initial-command=' + initial]


def wallpaper(root, mode):
    from install_support import apply_changes
    from macos_settings import ghostty_config
    root = Path(root)
    runtime_path = root / 'runtime.json'
    runtime = json.loads(runtime_path.read_text(encoding='utf-8'))
    if mode == 'status':
        return runtime['wallpaper']
    runtime['wallpaper'] = mode == 'on'
    if runtime['wallpaper'] and not (root / 'assets/b1scu1tk1d-landscape.png').is_file():
        raise ValueError('Bundled wallpaper missing. Reinstall Magik Terminal.')
    changes = {
        runtime_path: (json.dumps(runtime, indent=2) + '\n').encode(),
        root / 'ghostty.conf': ghostty_config(root, runtime).encode(),
    }
    apply_changes(changes, root / 'install-state.json')
    return runtime['wallpaper']


def main():
    try:
        mode = wallpaper_action(sys.argv[1:])
        if mode:
            enabled = wallpaper(ROOT, mode)
            print(TITLE + ' wallpaper: ' + ('on' if enabled else 'off') +
                  '. Saved. Reopen the Magik window to apply.')
            return 0
        runtime = json.loads((ROOT / 'runtime.json').read_text(encoding='utf-8'))
        invocation = command(sys.argv[1:], runtime,
                             interactive=sys.stdin.isatty() and sys.stdout.isatty(),
                             in_profile=os.environ.get('MAGIK_PROFILE') == str(ROOT))
        # Native passthrough replaces the wrapper, preserving POSIX signals/I/O.
        if invocation[0] != '/usr/bin/open':
            os.execvpe(invocation[0], invocation, os.environ)
        return subprocess.call(invocation)
    except (OSError, ValueError, KeyError) as error:
        print(f'Magik launch failed: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
