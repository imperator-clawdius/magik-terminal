"""Build the isolated Ghostty configuration without changing ordinary Ghostty."""
from pathlib import Path
import shlex

from theme_settings import TITLE


def value(text):
    text = str(text)
    if '\n' in text or '\r' in text:
        raise ValueError('Configuration values cannot contain newlines')
    return '"' + text.replace('\\', '\\\\').replace('"', '\\"') + '"'


def ghostty_config(root, runtime):
    root = Path(root)
    p = runtime['palette']
    palette = [p['panel'], p['rose'], p['cyan'], p['amber'], p['blue'], p['magenta'],
               p['cyan'], p['cream'], p['mute'], p['rose'], p['green'], '#f8d596',
               p['blue'], p['magenta'], '#9bf3e4', '#ffffff']
    fields = [
        '# ' + TITLE + ' - separate macOS instance',
        'title = ' + value(TITLE), 'font-family = Menlo', 'font-size = 12',
        'background = ' + p['ink'], 'foreground = ' + p['cream'],
        'cursor-color = ' + p['amber'], 'cursor-style = bar',
        'selection-background = #29443e', 'selection-foreground = ' + p['cream'],
        'window-padding-x = 24', 'window-padding-y = 8',
        'window-save-state = never', 'quit-after-last-window-closed = true',
        'window-colorspace = srgb', 'background-opacity = 1',
        'custom-shader = ' + value(root / runtime['shader']),
        'custom-shader-animation = ' + ('false' if runtime['no_motion'] else 'true'),
        'background-image-opacity = 0.10', 'background-image-position = center',
        'background-image-fit = cover', 'background-image-repeat = false',
        'background-image = ' + (value(root / 'assets/b1scu1tk1d-landscape.png') if runtime['wallpaper'] else ''),
        'command = ' + value(shlex.join([runtime['python'], str(root / 'session.py')])),
    ]
    fields.extend(f'palette = {i}={color}' for i, color in enumerate(palette))
    return '\n'.join(fields) + '\n'
