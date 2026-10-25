#!/usr/bin/env python3
"""Record the Zapret2 candidate binary identity, size and dynamic dependencies."""

import argparse
import json
import re
from pathlib import Path


ALLOWED = {
    "libc.so.0",
    "libm.so.0",
    "libz.so.1",
    "libgcc_s.so.1",
    "ld-uClibc.so.0",
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("binary", type=Path)
    parser.add_argument("readelf_dynamic", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    data = args.binary.read_bytes()
    if data[:4] != b"\x7fELF" or data[4] != 1 or data[5] != 1:
        raise SystemExit("candidate is not a 32-bit little-endian ELF")
    machine = int.from_bytes(data[18:20], "little")
    if machine != 8:
        raise SystemExit(f"candidate is not MIPS (e_machine={machine})")

    needed = sorted(set(re.findall(r"\(NEEDED\)\s+Shared library: \[([^\]]+)\]",
                                   args.readelf_dynamic.read_text(encoding="utf-8"))))
    unexpected = [name for name in needed if name not in ALLOWED]
    if unexpected:
        raise SystemExit(f"unexpected dynamic dependencies: {unexpected}")

    report = {
        "file": args.binary.name,
        "bytes": len(data),
        "elf": "32-bit LSB MIPS",
        "needed": needed,
        "scope": "candidate build only; not included in any firmware image",
    }
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"PASS {args.binary.name}: {len(data)} bytes; NEEDED={needed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
