"""Validate Ghostty GLSL with glslangValidator (developer/CI dependency)."""
from pathlib import Path
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
source = (root / 'macos/magik.glsl').read_text()
header = '''#version 330 core
uniform sampler2D iChannel0;
uniform vec3 iResolution;
uniform vec4 iCurrentCursor;
uniform float iTime;
out vec4 fragColor;
'''
with tempfile.TemporaryDirectory() as tmp:
    for name, define in [('animated', ''), ('still', '#define W1_STILL 1\n')]:
        path = Path(tmp) / (name + '.frag')
        path.write_text(header + define + source + '\nvoid main() { mainImage(fragColor, gl_FragCoord.xy); }\n')
        subprocess.run(['glslangValidator', '-S', 'frag', str(path)], check=True)
        print(name + ' Ghostty shader validated.')
