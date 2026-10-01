"""Compile the shader using Windows' actual D3D compiler (no SDK required)."""
import ctypes
from pathlib import Path
import sys

if sys.platform != 'win32':
    raise SystemExit('Shader compilation requires Windows.')
source = (Path(__file__).resolve().parents[1] / 'windows/magik.hlsl').read_bytes()
compiler = ctypes.WinDLL('d3dcompiler_47.dll')
compile_shader = compiler.D3DCompile
compile_shader.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_char_p,
    ctypes.c_void_p, ctypes.c_void_p, ctypes.c_char_p, ctypes.c_char_p,
    ctypes.c_uint, ctypes.c_uint, ctypes.POINTER(ctypes.c_void_p), ctypes.POINTER(ctypes.c_void_p)]
compile_shader.restype = ctypes.c_long
for variant, data in [('animated', source), ('still', b'#define W1_STILL 1\n' + source)]:
    code, errors = ctypes.c_void_p(), ctypes.c_void_p()
    result = compile_shader(data, len(data), b'magik.hlsl', None, None,
                            b'main', b'ps_4_0', 0, 0, ctypes.byref(code), ctypes.byref(errors))
    if errors.value:
        table = ctypes.cast(errors, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p))).contents
        get_pointer = ctypes.WINFUNCTYPE(ctypes.c_void_p, ctypes.c_void_p)(table[3])
        print(ctypes.string_at(get_pointer(errors)).decode())
    if result < 0:
        raise SystemExit(f'{variant} shader compilation failed: {result}')
    print(f'{variant} shader compiled successfully for ps_4_0.')
