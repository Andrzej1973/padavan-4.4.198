#!/usr/bin/env python3
"""Carry the checked CLOSING removal admission into an isolated MT7603 tree."""

import argparse
import shutil
from pathlib import Path


OLD = b"(r->phase==WR_REF_RESERVED||r->phase==WR_REF_UNCERTAIN_OPEN))return 0;"
NEW = (
    b"(r->phase==WR_REF_RESERVED||r->phase==WR_REF_CLOSING||\n"
    b"     r->phase==WR_REF_UNCERTAIN_OPEN))return 0;"
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if not args.source.is_dir() or args.output.exists():
        parser.error("source must exist and output must not exist")
    source_file = args.source / "include/interface-registry.h"
    data = source_file.read_bytes()
    newline = b"\r\n" if b"\r\n" in data else b"\n"
    replacement = NEW.replace(b"\n", newline)
    if data.count(OLD) != 1:
        parser.error("expected exactly one removal-admission anchor")
    shutil.copytree(args.source, args.output)
    (args.output / "include/interface-registry.h").write_bytes(
        data.replace(OLD, replacement, 1)
    )


if __name__ == "__main__":
    main()
