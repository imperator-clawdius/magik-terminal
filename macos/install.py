#!/usr/bin/env python3
"""Install a separate Magik Terminal instance for macOS / Ghostty."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from theme_settings import TITLE
from macos.settings import ghostty_config

spec = importlib.util.spec_from_file_location('magik_install_support', ROOT / 'install.py')
support = importlib.util.module_from_spec(spec)
spec.loader.exec_module(support)


def native_command(destination, override=None):
    saved = destination / 'runtime.json'
    if saved.exists() and not override:
        native = json.loads(saved.read_text())['native']
        if Path(native[0]).is_file():
            return native
    found = override or shutil.which('codex')
    if not found:
        raise ValueError('Install and sign into Codex CLI first, or pass --codex-executable.')
    path = Path(found).expanduser().absolute()
    if path == Path.home() / '.local/bin/codex' and not override:
        raise ValueError('Found a shim without saved native runtime. Supply --codex-executable with the real Codex path.')
    if not path.is_file() or not os.access(path, os.X_OK):
        raise ValueError('Native Codex path must be an executable file.')
    # Keep npm's symlink path: its env-node entry uses the captured PATH.
    return [str(path)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--wallpaper', choices=['on', 'off'])
    parser.add_argument('--no-motion', action='store_true', default=None)
    parser.add_argument('--motion', action='store_false', dest='no_motion')
    parser.add_argument('--uninstall', action='store_true')
    parser.add_argument('--no-shell-hook', action='store_true')
    parser.add_argument('--ghostty-app', type=Path)
    parser.add_argument('--codex-executable')
    args = parser.parse_args()
    if sys.platform != 'darwin':
        parser.error('This installer is for macOS. On Windows use install.ps1.')
    codex_home = Path(os.environ.get('CODEX_HOME', str(Path.home() / '.codex'))).resolve()
    destination = codex_home / 'magik-terminal-macos'
    state_path = destination / 'install-state.json'
    if args.uninstall:
        return support.uninstall(state_path)
    ghostty = args.ghostty_app or next((p for p in [Path('/Applications/Ghostty.app'),
                Path.home() / 'Applications/Ghostty.app'] if p.is_dir()), None)
    if ghostty is None or not (ghostty / 'Contents/MacOS/ghostty').is_file():
        parser.error('Install Ghostty first or pass --ghostty-app /path/to/Ghostty.app.')
    native = native_command(destination, args.codex_executable)
    saved = json.loads((destination / 'runtime.json').read_text()) if (destination / 'runtime.json').exists() else {}
    no_motion = args.no_motion if args.no_motion is not None else saved.get('no_motion', False)
    shader = (ROOT / 'macos/magik.glsl').read_bytes()
    if no_motion:
        shader = b'#define W1_STILL 1\n' + shader
    shader_name = 'magik-' + support.digest(shader)[:12] + '.glsl'
    runtime = dict(native=native, python=sys.executable, ghostty_app=str(ghostty.resolve()),
                   codex_home=str(codex_home), path=os.environ.get('PATH', ''),
                   wallpaper=args.wallpaper == 'on' if args.wallpaper else saved.get('wallpaper', False),
                   no_motion=no_motion, shader=shader_name,
                   palette=json.loads((ROOT / 'palette.json').read_text()))
    changes = {
        codex_home / 'config.toml': support.theme_config(support.text_at(codex_home / 'config.toml'), replace_welcome=True).encode(),
        codex_home / 'themes/widowmaker.tmTheme': support.theme_bytes(runtime['palette']),
        destination / 'runtime.json': (json.dumps(runtime, indent=2) + '\n').encode(),
        destination / 'ghostty.conf': ghostty_config(destination, runtime).encode(),
        destination / shader_name: shader,
    }
    for target, source in [('cli.py', 'macos/cli.py'), ('session.py', 'macos/session.py'),
                           ('macos_settings.py', 'macos/settings.py'), ('theme_settings.py', 'theme_settings.py'),
                           ('windows_cli.py', 'windows/cli.py'), ('install_support.py', 'install.py'),
                           ('assets/b1scu1tk1d-landscape.png', 'assets/b1scu1tk1d-landscape.png')]:
        changes[destination / target] = (ROOT / source).read_bytes()
    shim = Path.home() / '.local/bin/codex'
    recorded = json.loads(state_path.read_text())['files'] if state_path.exists() else {}
    if (shim.exists() or shim.is_symlink()) and str(shim) not in recorded:
        parser.error(f'Existing command at {shim}; move it or choose a different setup before installing.')
    changes[shim] = ('#!/bin/sh\nexec ' + shlex.join([sys.executable, str(destination / 'cli.py')]) + ' "$@"\n').encode()
    if not args.no_shell_hook:
        # macOS defaults to zsh; both interactive shells receive the shim first.
        line = 'export PATH=' + shlex.quote(str(shim.parent)) + ':"$PATH"'
        for name in ['.zshrc', '.bash_profile']:
            path = Path.home() / name
            changes[path] = support.managed_block(support.text_at(path), line).encode()
    support.apply_changes(changes, state_path)
    shim.chmod(0o755)
    # The config parser can run without a graphical session. A render-thread
    # shader failure is a separate condition; compile it in CI as well.
    check = subprocess.run([str(ghostty / 'Contents/MacOS/ghostty'), '+validate-config',
                            '--config-file=' + str(destination / 'ghostty.conf')],
                           capture_output=True, text=True)
    if check.returncode:
        print('Ghostty config validation failed. Saved backups are available for uninstall.', file=sys.stderr)
        print(check.stdout + check.stderr, file=sys.stderr)
        return check.returncode
    print(TITLE + ' installed for macOS (Ghostty).')
    print('Open a new shell, then: codex --magik | codex --magik --yolo')
    print('Wallpaper: codex --magik --wallpaper on|off|status. Reopen Magik to apply.')
    print('Ordinary Ghostty configuration remains separate. Backups: ' + str(state_path))
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError) as error:
        print(f'Mac install failed: {error}', file=sys.stderr)
        sys.exit(1)
