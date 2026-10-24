#!/usr/bin/env python3
"""Regression: dlopen libraries need closure checks, not executable PT_INTERP."""
import importlib.util
from pathlib import Path
import struct
import subprocess
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("closure", Path(__file__).parent / "band-steering/verify-package-closure.py")
closure = importlib.util.module_from_spec(spec)
spec.loader.exec_module(closure)
root = Path("/virtual-image")

def elf(kind):
    data = bytearray(52)
    data[:7] = b"\x7fELF\x01\x01\x01"
    struct.pack_into("<HH", data, 16, kind, 8)
    return bytes(data)

files = {"usr/bin/lua": elf(2), "lib/libc.so.0": elf(3),
         "lib/ld.so": elf(3), "etc_ro/lua/5.1/lib/cjson.so": elf(3)}

def resolve(base, relative):
    if relative not in files:
        raise ValueError("Missing image file: " + relative)
    return root / relative

def readelf(argv, **kwargs):
    relative = Path(argv[-1]).relative_to(root).as_posix()
    if argv[1] == "-d":
        return "(NEEDED) Shared library: [libc.so.0]" if relative in ("usr/bin/lua", "etc_ro/lua/5.1/lib/cjson.so") else ""
    return "[Requesting program interpreter: /lib/ld.so]" if relative == "usr/bin/lua" else ""

with patch.object(closure, "resolve_image", resolve), patch.object(Path, "read_bytes", lambda p: files[p.relative_to(root).as_posix()]), patch.object(subprocess, "check_output", readelf):
    result = closure.verify(root, root, "readelf", ["usr/bin/lua"], shared_libraries=["etc_ro/lua/5.1/lib/cjson.so"])
    assert "image:etc_ro/lua/5.1/lib/cjson.so" in result
    assert "image:lib/libc.so.0" in result and "image:lib/ld.so" in result
    try:
        closure.verify(root, root, "readelf", ["etc_ro/lua/5.1/lib/cjson.so"])
    except ValueError as e:
        assert "no interpreter" in str(e)
    else:
        raise AssertionError("Executable interpreter guard weakened")
    del files["lib/libc.so.0"]
    try:
        closure.verify(root, root, "readelf", ["usr/bin/lua"], shared_libraries=["etc_ro/lua/5.1/lib/cjson.so"])
    except ValueError as e:
        assert "Missing libc.so.0" in str(e)
    else:
        raise AssertionError("Missing dependency accepted")
    files["lib/libc.so.0"] = elf(3)
    try:
        closure.verify(root, root, "readelf", ["usr/bin/lua"], shared_libraries=["../outside.so"])
    except ValueError as e:
        assert "stay relative" in str(e)
    else:
        raise AssertionError("Unsafe library path accepted")
print("PASS: shared-library closure; strict executable interpreter, missing dependency and path guards")
