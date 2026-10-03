#!/usr/bin/env python3
"""Verify USBIP's ELF dependency closure inside the target ROMFS."""
import json
import os
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath

root = Path(sys.argv[1]).absolute()
output = Path(sys.argv[2])

def resolve_target(name):
    parts = list(PurePosixPath(name).parts)
    if parts and parts[0] == "/":
        parts.pop(0)
    done = []
    links = 0
    while parts:
        part = parts.pop(0)
        if part in ("", "."):
            continue
        if part == "..":
            if not done:
                raise RuntimeError("Path escapes ROMFS: " + name)
            done.pop()
            continue
        candidate = root.joinpath(*done, part)
        if candidate.is_symlink():
            links += 1
            if links > 40:
                raise RuntimeError("Symlink loop: " + name)
            target = os.readlink(candidate)
            if target.startswith("/"):
                done = []
            parts = [p for p in PurePosixPath(target).parts if p != "/"] + parts
        else:
            done.append(part)
    result = root.joinpath(*done)
    if not result.is_file():
        raise RuntimeError("Missing ROMFS file: " + name)
    return result

def readelf(option, path):
    return subprocess.check_output(["readelf", option, str(path)], text=True,
                                   env=dict(os.environ, LC_ALL="C"))

pending = ["/sbin/usbip", "/sbin/usbipd", "/lib/libudev.so.1"]
seen = set()
report = []
while pending:
    name = pending.pop()
    path = resolve_target(name)
    if path in seen:
        continue
    seen.add(path)
    header = readelf("-h", path)
    if not re.search(r"Machine:.*MIPS", header):
        raise RuntimeError("Non-MIPS ELF: " + name)
    if not re.search(r"Class:.*ELF32", header) or "little endian" not in header:
        raise RuntimeError("Incorrect ELF class/byte order: " + name)
    program = readelf("-l", path)
    interpreter = re.search(r"Requesting program interpreter: ([^\]]+)", program)
    if interpreter:
        pending.append(interpreter.group(1))
    dynamic = readelf("-d", path)
    needed = re.findall(r"\(NEEDED\).*\[([^\]]+)\]", dynamic)
    for library in needed:
        if "/" in library:
            raise RuntimeError("Unexpected dependency path: " + library)
        for directory in ("/lib/", "/usr/lib/"):
            try:
                resolve_target(directory + library)
            except RuntimeError:
                continue
            pending.append(directory + library)
            break
        else:
            raise RuntimeError(name + " needs missing " + library)
    report.append({"path": name, "resolved": "/" + path.relative_to(root).as_posix(),
                   "needed": needed,
                   "interpreter": interpreter.group(1) if interpreter else None})
output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print("USBIP ELF dependency closure verified:", len(report), "files")
