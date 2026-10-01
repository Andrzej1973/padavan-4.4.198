#!/usr/bin/env python3
"""Repair invalid event masks in the pinned Padavan 4.4 web configuration."""
from pathlib import Path
import re
import sys

path = Path(sys.argv[1]) / "trunk/user/httpd/common.h"
text = path.read_text()
changes = {
    "EVM_RESTART_REBOOT": (64, 16),
    "EVM_BLOCK_UNSAFE": (65, 54),
}
occupied = {
    int(bit): name for name, bit in re.findall(
        r"^#define\s+(EVM_\w+)\s+\(1ULL\s*<<\s*(\d+)\)", text, re.M)
}
for name, (old, new) in changes.items():
    if new in occupied:
        raise SystemExit(f"Event bit {new} is occupied by {occupied[new]}")
    pattern = rf"(^#define\s+{name}\s+)\(1ULL\s*<<\s*{old}\)"
    text, count = re.subn(pattern, lambda m: m.group(1) + f"(1ULL << {new})",
                          text, flags=re.M)
    if count != 1:
        raise SystemExit(f"Unexpected definition for {name}")
bits = [int(bit) for bit in re.findall(r"^#define\s+EVM_\w+\s+\(1ULL\s*<<\s*(\d+)\)", text, re.M)]
if len(bits) != len(set(bits)) or any(bit >= 64 for bit in bits):
    raise SystemExit("Invalid or duplicate event bits")
path.write_text(text)
print("Validated", len(bits), "distinct event bits below 64")
