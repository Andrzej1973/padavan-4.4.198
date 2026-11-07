#!/usr/bin/env python3
"""Verify the pinned Zapret2 source snapshot without contacting upstream."""

import hashlib
import json
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
BASE = REPO / "third_party" / "bol-van"
SOURCE = BASE / "zapret2"
MANIFEST = BASE / "zapret2-source-manifest.json"


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    entries = manifest["files"]
    if len(entries) != manifest["file_count"]:
        raise ValueError("manifest file_count differs from entry count")
    expected = {}
    for item in entries:
        rel = Path(item["path"])
        if rel.is_absolute() or ".." in rel.parts or item["path"] in expected:
            raise ValueError(f"unsafe or repeated manifest path: {item['path']}")
        expected[item["path"]] = item

    actual = {}
    for path in SOURCE.rglob("*"):
        if path.is_symlink():
            raise ValueError(f"unexpected symlink: {path}")
        if path.is_file():
            actual[path.relative_to(SOURCE).as_posix()] = path

    errors = []
    for name in sorted(expected.keys() - actual.keys()):
        errors.append(f"missing: {name}")
    for name in sorted(actual.keys() - expected.keys()):
        errors.append(f"extra: {name}")
    total = 0
    for name in sorted(expected.keys() & actual.keys()):
        data = actual[name].read_bytes()
        total += len(data)
        item = expected[name]
        if len(data) != item["size"] or hashlib.sha256(data).hexdigest() != item["sha256"]:
            errors.append(f"modified: {name}")
    if errors:
        print("Zapret2 source verification failed:\n" + "\n".join(errors), file=sys.stderr)
        return 1
    print(f"Zapret2 source verified: {len(actual)} files, {total} bytes, commit {manifest['commit']}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (KeyError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"Zapret2 source verification failed: {exc}", file=sys.stderr)
        sys.exit(1)
