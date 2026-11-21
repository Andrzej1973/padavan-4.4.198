#!/usr/bin/env python3
"""Verify the pinned netfilter dependency archives without extracting them."""

import hashlib
import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
BASE = REPO / "third_party" / "netfilter"
MANIFEST = BASE / "SOURCE-MANIFEST.json"


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    packages = manifest["packages"]
    if not packages:
        raise ValueError("manifest has no packages")

    seen = set()
    total = 0
    for item in packages:
        name = item["archive"]
        if name in seen:
            raise ValueError(f"repeated archive entry: {name}")
        seen.add(name)
        path = BASE / name
        if not path.is_file():
            raise ValueError(f"missing archive: {name}")
        data = path.read_bytes()
        if len(data) != item["bytes"]:
            raise ValueError(f"size mismatch: {name}")
        digest = hashlib.sha256(data).hexdigest()
        if digest != item["sha256"]:
            raise ValueError(f"sha256 mismatch: {name}")
        total += len(data)
        print(f"PASS {item['name']} {item['version']} {len(data)} bytes")

    allowed = seen | {MANIFEST.name}
    extra = sorted(p.name for p in BASE.iterdir() if p.is_file() and p.name not in allowed)
    if extra:
        raise ValueError(f"unexpected files in vendor directory: {extra}")

    print(f"PASS {len(seen)} pinned archives, {total} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
