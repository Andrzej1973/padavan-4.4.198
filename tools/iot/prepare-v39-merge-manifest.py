#!/usr/bin/env python3
"""Pin isolated v39 overlay records against the reviewed MT7603 source."""

import argparse
import hashlib
import json
from pathlib import Path

SOURCE_DIRS = frozenset({"ap", "common", "hw_ctrl", "include", "mac", "mcu", "os", "tx_rx"})
REVISION = "c25283e915a2a00a763774dd255b14aff997285e"


def blob(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pinned_driver", type=Path)
    parser.add_argument("candidate_driver", type=Path)
    parser.add_argument("reviewed_manifest", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output already exists")
    reviewed = json.loads(args.reviewed_manifest.read_text(encoding="utf-8"))
    if reviewed.get("source_revision") != REVISION:
        parser.error("reviewed source revision differs")
    old_blobs = reviewed.get("source_git_blobs")
    if not isinstance(old_blobs, dict) or len(old_blobs) not in (31, 36):
        parser.error("reviewed source blob inventory differs")
    for name, expected in old_blobs.items():
        path = args.pinned_driver / name
        if not path.is_file() or blob(path.read_bytes()) != expected:
            parser.error(f"reviewed pinned source differs: {name}")
    files = []
    originals = {}
    for path in sorted(args.candidate_driver.rglob("*")):
        if not path.is_file():
            continue
        name = path.relative_to(args.candidate_driver).as_posix()
        if name == "manifest.json":
            continue
        files.append({"path": name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
        if name.split("/", 1)[0] in SOURCE_DIRS:
            original = args.pinned_driver / name
            if original.is_file():
                originals[name] = blob(original.read_bytes())
    overlay_count = sum(item["path"].split("/", 1)[0] in SOURCE_DIRS for item in files)
    if overlay_count != 56 or len(originals) != 37 or not set(old_blobs).issubset(originals):
        parser.error("v39 source inventory changed; review before assembly")
    manifest = {"schema": 1, "source_revision": REVISION,
                "source_git_blobs": originals, "files": files,
                "target_compiled": False, "production_installed": False,
                "runtime_verified": False}
    args.output.write_bytes((json.dumps(manifest, indent=2) + "\n").encode("utf-8"))
    print(f"Pinned {overlay_count} source paths and {len(originals)} original blobs")


if __name__ == "__main__":
    main()
