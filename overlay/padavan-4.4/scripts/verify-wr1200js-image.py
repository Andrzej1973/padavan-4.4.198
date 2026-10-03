#!/usr/bin/env python3
"""Read-only uImage checks matching Padavan HTTP upload criteria.

This checks image structure, not bootability or live-router flash capacity.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import zlib

parser = argparse.ArgumentParser()
parser.add_argument("image", type=Path)
parser.add_argument("--report", type=Path, required=True)
parser.add_argument("--max-size", type=int, default=16187392)
args = parser.parse_args()
data = args.image.read_bytes()
if len(data) < 64:
    raise SystemExit("Image is shorter than a uImage header")
magic, hcrc, timestamp, payload_size, load, entry, dcrc, os_id, arch, image_type, compression, name = struct.unpack(
    ">7I4B32s", data[:64])
header = bytearray(data[:64])
header[4:8] = b"\0" * 4
checks = {
    "uimage_magic": magic == 0x27051956,
    "product_id": data[36:44] == b"WR1200JS",
    "header_crc": (zlib.crc32(header) & 0xffffffff) == hcrc,
    "declared_length": payload_size + 64 == len(data),
    "payload_crc": (zlib.crc32(data[64:64 + payload_size]) & 0xffffffff) == dcrc,
    "size_range": 64 + 2 * 1024 * 1024 <= len(data) <= args.max_size,
}
report = {
    "scope": "Padavan uImage upload structure; device boot unverified",
    "image": args.image.name,
    "bytes": len(data),
    "sha256": hashlib.sha256(data).hexdigest(),
    "declared_payload_bytes": payload_size,
    "architecture_id": arch,
    "compression_id": compression,
    "checks": checks,
}
args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
failed = [key for key, passed in checks.items() if not passed]
if failed:
    raise SystemExit("Firmware structure rejected: " + ", ".join(failed))
print("WR1200JS image structure checks passed; boot remains unverified")
