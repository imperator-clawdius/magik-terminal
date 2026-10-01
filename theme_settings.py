"""Shared, offline theme settings for the installer and command wrapper."""
import hashlib
import json
from pathlib import Path
import re

TITLE = 'Magik Terminal for Codex (By W1d0wm4k3r)'
GUID = '{89a85927-87d9-4b07-922a-3fc6a9f2dc61}'
WALLPAPER_OPACITY = 0.10


def jsonc(text):
    """Read Terminal JSONC without interpreting comments inside strings."""
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
        else:
            out.append(ch)
        i += 1
    clean = ''.join(out)
    clean = re.sub(r'("(?:\\.|[^"\\])*"\s*)|,\s*(?=[}\]])',
                   lambda m: m.group(1) or '', clean)
    return json.loads(clean.lstrip('\ufeff'))


def wallpaper_properties(asset, enabled):
    return {
        'backgroundImage': str(asset) if enabled else None,
        'backgroundImageOpacity': WALLPAPER_OPACITY if enabled else 0,
        'backgroundImageStretchMode': 'uniformToFill',
        'backgroundImageAlignment': 'center',
    }


def wallpaper_action(args):
    """Wallpaper is a settings-only command, never a model prompt."""
    prefix = args[:args.index('--')] if '--' in args else args
    if not any(x in prefix for x in ('--magik', '--widowmaker')) or '--wallpaper' not in prefix:
        return None
    rest = [x for x in args if x not in ('--magik', '--widowmaker')]
    if len(rest) != 2 or rest[0] != '--wallpaper' or rest[1] not in ('on', 'off', 'status'):
        raise ValueError('Use codex --magik --wallpaper on|off|status without other Codex arguments.')
    return rest[1]


def set_wallpaper(root, mode):
    root = Path(root)
    runtime_path = root / 'runtime.json'
    runtime = json.loads(runtime_path.read_text(encoding='utf-8'))
    settings_path = Path(runtime['terminal_settings'])
    data = jsonc(settings_path.read_text(encoding='utf-8-sig'))
    profiles = data.get('profiles', {})
    items = profiles if isinstance(profiles, list) else profiles.get('list', [])
    profile = next((p for p in items if p.get('guid', '').lower() == GUID), None)
    if profile is None:
        raise ValueError('Magik Terminal profile is missing. Reinstall the theme.')
    if mode == 'status':
        return bool(profile.get('backgroundImage') and profile.get('backgroundImageOpacity', 1) > 0)
    if mode not in ('on', 'off'):
        raise ValueError('Wallpaper mode must be on, off, or status.')
    enabled = mode == 'on'
    asset = root / 'assets/b1scu1tk1d-landscape.png'
    if enabled and not asset.is_file():
        raise ValueError('Bundled wallpaper is missing. Reinstall the theme.')
    profile.update(wallpaper_properties(asset, enabled))
    runtime['wallpaper'] = enabled
    state_path = root / 'install-state.json'
    state = json.loads(state_path.read_text(encoding='utf-8'))
    changes = {settings_path: (json.dumps(data, indent=4) + '\n').encode(),
               runtime_path: (json.dumps(runtime, indent=2) + '\n').encode()}
    old = {p: p.read_bytes() for p in changes}
    for path, content in changes.items():
        record = state['files'].get(str(path))
        if record:
            # A user's unrelated later edits must never be silently rolled back
            # by uninstall, even if they subsequently toggle the wallpaper.
            if hashlib.sha256(old[path]).hexdigest() != record['installed_sha256']:
                record['user_modified'] = True
            record['installed_sha256'] = hashlib.sha256(content).hexdigest()
    changes[state_path] = (json.dumps(state, indent=2) + '\n').encode()
    old[state_path] = state_path.read_bytes()
    written = []
    try:
        for path, content in changes.items():
            path.write_bytes(content)
            written.append(path)
    except OSError:
        for path in reversed(written):
            path.write_bytes(old[path])
        raise
    return enabled
