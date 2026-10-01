#!/usr/bin/env python3
"""Magik Terminal installer. Python 3.11+, standard library only."""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import plistlib
import re
import shutil
import subprocess
import sys
import tomllib

ROOT = Path(__file__).resolve().parent
GUID = '{89a85927-87d9-4b07-922a-3fc6a9f2dc61}'
START = '# >>> Magik Terminal >>>'
END = '# <<< Magik Terminal <<<'


def jsonc(text):
    """Read Terminal JSONC without interpreting comment markers inside strings."""
    out, i, quoted = [], 0, False
    while i < len(text):
        ch = text[i]
        if quoted:
            out.append(ch)
            if ch == '\\' and i + 1 < len(text):
                i += 1
                out.append(text[i])
            elif ch == '"':
                quoted = False
        elif ch == '"':
            quoted = True
            out.append(ch)
        elif text[i:i+2] == '//':
            end = text.find('\n', i)
            i = len(text) if end < 0 else end
            continue
        elif text[i:i+2] == '/*':
            end = text.find('*/', i+2)
            if end < 0:
                raise ValueError('Unclosed JSONC comment')
            out.append(' ')
            i = end + 2
            continue
        elif ch == ',':
            # Remove trailing commas after comments have been stripped below.
            out.append(ch)
        else:
            out.append(ch)
        i += 1
    clean = ''.join(out)
    # The string alternative shields commas inside JSON strings.
    clean = re.sub(r'("(?:\\.|[^"\\])*"\s*)|,\s*(?=[}\]])',
                   lambda m: m.group(1) or '', clean)
    return json.loads(clean.lstrip('\ufeff'))


def theme_config(text):
    """Surgical edit, with TOML validation before and after."""
    before = tomllib.loads(text)
    lines = text.splitlines(keepends=True)
    start = next((i for i, line in enumerate(lines)
                  if re.match(r'^\s*\[tui\]\s*(?:#.*)?$', line.strip())), None)
    if start is None:
        # Avoid silently corrupting inline/dotted TUI tables.
        if 'tui' in before:
            raise ValueError('Use a [tui] table in config.toml before installing Magik.')
        result = text.rstrip() + '\n\n[tui]\ntheme = "magik"\n'
    else:
        end = next((i for i in range(start+1, len(lines))
                    if re.match(r'^\s*\[', lines[i])), len(lines))
        found = next((i for i in range(start+1, end)
                      if re.match(r'^\s*theme\s*=', lines[i])), None)
        if found is None:
            lines.insert(start+1, 'theme = "magik"\n')
        else:
            lines[found] = 'theme = "magik"\n'
        result = ''.join(lines)
    after = tomllib.loads(result)
    expected = dict(before)
    expected['tui'] = {**before.get('tui', {}), 'theme': 'magik'}
    if after != expected:
        raise ValueError('Refusing to alter unrelated Codex settings')
    return result


def managed_block(text, body):
    block = START + '\n' + body.rstrip() + '\n' + END
    pattern = re.escape(START) + r'.*?' + re.escape(END)
    if START in text:
        if END not in text or text.count(START) != 1:
            raise ValueError('Malformed Magik profile block')
        return re.sub(pattern, lambda _: block, text, flags=re.S)
    return text.rstrip() + '\n\n' + block + '\n'


def text_at(path):
    if not path.exists():
        return ''
    raw = path.read_bytes()
    if raw.startswith((b'\xff\xfe', b'\xfe\xff')):
        return raw.decode('utf-16')
    return raw.decode('utf-8-sig')


def theme_bytes(p):
    settings = [{'settings': {'background': p['ink'], 'foreground': p['cream'],
                             'caret': p['amber'], 'selection': '#29443e',
                             'lineHighlight': p['panel']}}]
    for name, scope, color in [
        ('Comments', 'comment, punctuation.definition.comment', 'mute'),
        ('Keywords', 'keyword, storage, storage.type', 'amber'),
        ('Strings', 'string, constant.other.symbol', 'cyan'),
        ('Numbers', 'constant.numeric, constant.language', 'magenta'),
        ('Functions', 'entity.name.function, support.function', 'amber'),
        ('Types', 'entity.name.type, entity.name.class, support.type', 'blue'),
        ('Variables', 'variable, meta.definition.variable', 'cream'),
        ('Headings', 'markup.heading, entity.name.section', 'amber'),
        ('Links', 'markup.underline.link', 'cyan'),
        ('Inserted', 'markup.inserted, diff.inserted', 'green'),
        ('Deleted', 'markup.deleted, diff.deleted', 'rose'),
        ('Invalid', 'invalid', 'rose'),
    ]:
        style = {'foreground': p[color]}
        if name == 'Inserted':
            style['background'] = '#12271f'
        elif name == 'Deleted':
            style['background'] = '#2c171e'
        settings.append({'name': name, 'scope': scope, 'settings': style})
    return plistlib.dumps({'name': 'Magik Terminal', 'settings': settings})


def scheme(p):
    return {'name': 'Magik Terminal', 'background': p['ink'], 'foreground': p['cream'],
            'cursorColor': p['amber'], 'selectionBackground': '#29443e',
            'black': p['panel'], 'red': p['rose'], 'green': p['cyan'],
            'yellow': p['amber'], 'blue': p['blue'], 'purple': p['magenta'],
            'cyan': p['cyan'], 'white': p['cream'], 'brightBlack': p['mute'],
            'brightRed': p['rose'], 'brightGreen': p['green'],
            'brightYellow': '#f8d596', 'brightBlue': p['blue'],
            'brightPurple': p['magenta'], 'brightCyan': '#9bf3e4', 'brightWhite': '#ffffff'}


def terminal_config(text, destination, p, no_motion=False, default_profile=False, shader_filename='magik.hlsl'):
    data = jsonc(text)
    profiles = data.setdefault('profiles', {'list': []})
    if isinstance(profiles, list):
        profiles = data['profiles'] = {'list': profiles}
    items = profiles.setdefault('list', [])
    existing = next((x for x in items if x.get('guid') == GUID), None)
    if any(x.get('name') == 'Magik Terminal' and x.get('guid') != GUID for x in items):
        raise ValueError('An unrelated Magik Terminal profile already exists')
    profile = {
        'guid': GUID, 'name': 'Magik Terminal', 'hidden': False,
        'commandline': f'powershell.exe -NoLogo -NoExit -File "{destination / "launch.ps1"}"',
        'startingDirectory': '%USERPROFILE%', 'tabTitle': 'Magik Terminal',
        'suppressApplicationTitle': True, 'colorScheme': 'Magik Terminal',
        'font': {'face': 'Cascadia Mono', 'size': 12},
        'padding': '24, 8, 24, 8', 'cursorShape': 'bar', 'tabColor': p['amber'],
    }
    if not no_motion:
        profile['experimental.pixelShaderPath'] = str(destination / shader_filename)
    if existing is not None:
        items[items.index(existing)] = profile
    else:
        items.append(profile)
    schemes = data.setdefault('schemes', [])
    schemes[:] = [x for x in schemes if x.get('name') != 'Magik Terminal'] + [scheme(p)]
    if default_profile:
        data['defaultProfile'] = GUID
    return json.dumps(data, indent=4) + '\n'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def apply_changes(changes, state_path):
    """Save originals before writes; roll back a failed install."""
    state = json.loads(state_path.read_text()) if state_path.exists() else {'files': {}}
    old_state = state_path.read_bytes() if state_path.exists() else None
    rollback = {}
    for path, content in changes.items():
        original = path.read_bytes() if path.exists() else None
        rollback[path] = original
        record = state['files'].setdefault(str(path), {
            'before': None if original is None else base64.b64encode(original).decode()})
        record['installed_sha256'] = digest(content)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(state, indent=2), encoding='utf-8')
    try:
        for path, content in changes.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
    except BaseException:
        failures = []
        for path, original in rollback.items():
            # Do not reopen an unchanged or inaccessible file that caused failure.
            current = path.read_bytes() if path.exists() else None
            if current == original:
                continue
            try:
                if original is None:
                    path.unlink(missing_ok=True)
                else:
                    path.write_bytes(original)
            except OSError as error:
                failures.append(f'{path}: {error}')
        if failures:
            raise OSError('Rollback incomplete; originals retained in ' + str(state_path) + ': ' + '; '.join(failures))
        if old_state is None:
            state_path.unlink(missing_ok=True)
        else:
            state_path.write_bytes(old_state)
        raise


def uninstall(state_path):
    if not state_path.exists():
        print('No Magik installation record found.')
        return 0
    state = json.loads(state_path.read_text())
    if state.get('path_added') and sys.platform == 'win32':
        update_user_path(state['path_added'], remove=True)
    retained = {}
    for filename, record in state['files'].items():
        path = Path(filename)
        if path.exists() and digest(path.read_bytes()) != record['installed_sha256']:
            retained[filename] = record
            print(f'Kept modified file: {path} (original remains in {state_path})')
            continue
        if record['before'] is None:
            path.unlink(missing_ok=True)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(base64.b64decode(record['before']))
    if retained:
        state['files'] = retained
        state_path.write_text(json.dumps(state, indent=2), encoding='utf-8')
        print('Partial uninstall: resolve the listed modified files using the saved originals.')
        return 2
    state_path.unlink()
    print('Magik removed. Original files restored. Restart your terminal.')
    return 0


def find_terminal():
    local = Path(os.environ['LOCALAPPDATA'])
    candidates = [
        local / 'Packages/Microsoft.WindowsTerminal_8wekyb3d8bbwe/LocalState/settings.json',
        local / 'Packages/Microsoft.WindowsTerminalPreview_8wekyb3d8bbwe/LocalState/settings.json',
        local / 'Microsoft/Windows Terminal/settings.json',
    ]
    return next((p for p in candidates if p.exists()), None)


def find_native(destination, override=None):
    runtime = destination / 'runtime.json'
    if runtime.exists() and not override:
        native = json.loads(runtime.read_text())['native']
        if all(Path(x).exists() for x in native):
            return native
    found = override or shutil.which('codex.exe') or shutil.which('codex.cmd') or shutil.which('codex')
    if not found:
        raise ValueError('Install Codex CLI and add it to PATH first.')
    found = Path(found).resolve()
    if found.suffix.lower() == '.exe':
        return [str(found)]
    npm_entry = found.parent / 'node_modules/@openai/codex/bin/codex.js'
    node = shutil.which('node.exe')
    if npm_entry.exists() and node:
        return [node, str(npm_entry)]
    raise ValueError('Cannot locate native Codex. Supply --codex-executable PATH to the real codex.exe.')


def update_user_path(directory, remove=False):
    import winreg
    import ctypes
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, 'Environment', 0, winreg.KEY_READ | winreg.KEY_SET_VALUE) as key:
        try:
            old, kind = winreg.QueryValueEx(key, 'Path')
        except FileNotFoundError:
            old, kind = '', winreg.REG_EXPAND_SZ
        parts = [p for p in old.split(';') if p]
        contains = lambda p: os.path.normcase(os.path.expandvars(p)).rstrip('\\/') == os.path.normcase(directory).rstrip('\\/')
        if remove:
            updated = ';'.join(p for p in parts if not contains(p))
        elif any(contains(p) for p in parts):
            return False
        else:
            updated = ';'.join([directory] + parts)
        winreg.SetValueEx(key, 'Path', 0, kind, updated)
    # Tell Explorer that newly launched shells need a fresh environment.
    result = ctypes.c_size_t()
    ctypes.windll.user32.SendMessageTimeoutW(0xffff, 0x1a, 0, 'Environment', 2, 1000, ctypes.byref(result))
    return not remove


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--no-motion', action='store_true', help='Install without the animated shader')
    parser.add_argument('--uninstall', action='store_true')
    parser.add_argument('--theme-only', action='store_true', help='Only install the Codex syntax theme')
    parser.add_argument('--no-shell-hook', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('--default-profile', action='store_true', help='Make Magik the default Windows Terminal profile')
    parser.add_argument('--codex-executable', help='Path to native codex.exe, for custom installations')
    parser.add_argument('--terminal-settings', type=Path, help='Explicit Windows Terminal settings.json')
    args = parser.parse_args()
    codex_home = Path(os.environ.get('CODEX_HOME', str(Path.home() / '.codex'))).resolve()
    destination = codex_home / 'magik-terminal'
    state_path = destination / 'install-state.json'
    if args.uninstall:
        return uninstall(state_path)
    p = json.loads((ROOT / 'palette.json').read_text())
    config = codex_home / 'config.toml'
    changes = {
        config: theme_config(text_at(config)).encode(),
        codex_home / 'themes/magik.tmTheme': theme_bytes(p),
    }
    if not args.theme_only:
        if sys.platform != 'win32':
            parser.error('Full integration requires Windows Terminal. Use --theme-only and themes/kitty.conf elsewhere.')
        native = find_native(destination, args.codex_executable)
        terminal = args.terminal_settings or find_terminal()
        if terminal is None:
            parser.error('Open Windows Terminal once, or supply --terminal-settings PATH.')
        for name in ['launch.ps1', 'cli.py']:
            changes[destination / name] = (ROOT / 'windows' / name).read_bytes()
        changes[destination / 'runtime.json'] = json.dumps({'native': native}, indent=2).encode()
        shader = (ROOT / 'windows/magik.hlsl').read_bytes()
        # Terminal caches shaders by path; a content-addressed name forces live
        # reload when a shader changes, without closing the user's running tab.
        shader_filename = f'magik-{digest(shader)[:12]}.hlsl'
        changes[destination / shader_filename] = shader
        changes[terminal] = terminal_config(text_at(terminal), destination, p, args.no_motion, args.default_profile, shader_filename).encode()
        # A PATH shim works in PowerShell and cmd without editing shell profiles.
        shim_dir = Path.home() / '.local/bin'
        escaped_python = sys.executable.replace("'", "''")
        escaped_cli = str(destination / 'cli.py').replace("'", "''")
        ps = f'''# Magik Terminal command shim. Native Codex remains unchanged.
if ($MyInvocation.ExpectingInput) {{
    $input | & '{escaped_python}' '{escaped_cli}' @args
}} else {{
    & '{escaped_python}' '{escaped_cli}' @args
}}
exit $LASTEXITCODE
'''
        cmd = f'@echo off\r\n@rem Magik Terminal command shim\r\n"{sys.executable}" "{destination / "cli.py"}" %*\r\nexit /b %errorlevel%\r\n'
        recorded_files = json.loads(state_path.read_text())['files'] if state_path.exists() else {}
        for name, content in [('codex.ps1', ps), ('codex.cmd', cmd)]:
            path = shim_dir / name
            if path.exists() and str(path) not in recorded_files:
                parser.error(f'Existing command at {path}; move it before installing to avoid a collision.')
            changes[path] = content.encode('utf-8-sig' if name.endswith('.ps1') else 'utf-8')
    apply_changes(changes, state_path)
    if not args.theme_only:
        if update_user_path(str(shim_dir)):
            state = json.loads(state_path.read_text())
            state['path_added'] = str(shim_dir)
            state_path.write_text(json.dumps(state, indent=2), encoding='utf-8')
    print('Magik Terminal installed. Codex theme: magik.')
    print(f'Original file backups: {state_path}')
    if not args.theme_only:
        print('Select Magik Terminal in Windows Terminal.')
        print('Commands: codex --magik | codex --magik --yolo')
        print('Plain codex passes through. Restart your terminal if PATH changed.')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        print(f'Install failed: {error}', file=sys.stderr)
        sys.exit(1)
