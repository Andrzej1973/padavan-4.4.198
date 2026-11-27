#!/usr/bin/env python3
"""Compare provenance reports from two independently executed WR1200JS builds."""
import argparse
import json
import re
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("first", type=Path)
parser.add_argument("second", type=Path)
parser.add_argument("--squashfs-reports", nargs=2, type=Path,
                    metavar=("FIRST", "SECOND"),
                    help="optional final-content reports for filesystem diagnostics")
args = parser.parse_args()
first = json.loads(args.first.read_text())
second = json.loads(args.second.read_text())
def run_identity(report):
    run = report.get("ci_run", {})
    if not isinstance(run, dict):
        raise SystemExit("Invalid CI run identity")
    repository, run_id, attempt = (run.get(key, "") for key in
                                   ("repository", "run_id", "run_attempt"))
    if (not isinstance(repository, str) or "/" not in repository
            or any(not isinstance(value, str) or not re.fullmatch(r"[1-9][0-9]*", value)
                   for value in (run_id, attempt))):
        raise SystemExit("Missing or invalid CI run identity")
    return repository.lower(), run_id, attempt


if run_identity(first) == run_identity(second):
    raise SystemExit("Both reports identify the same CI run attempt")
inputs = ("source_sha", "firmware_build_number", "sqm_profile", "toolchain_variant", "compiler_sha256",
          "readelf_sha256", "build_host", "kernel_build_metadata", "input_sha256")
differences = [key for key in inputs if not first.get(key) or first[key] != second.get(key)]
if first.get("compiler_cache_mode") != second.get("compiler_cache_mode"):
    differences.append("compiler_cache_mode")
if differences:
    raise SystemExit("Build inputs differ or are missing: " + ", ".join(differences))
digests = [report.get("image_sha256", "") for report in (first, second)]
if any(not re.fullmatch(r"[0-9a-f]{64}", digest) for digest in digests):
    raise SystemExit("Missing or invalid TRX SHA-256")
filesystems = []
if args.squashfs_reports:
    filesystems = [json.loads(path.read_text()) for path in args.squashfs_reports]
    if [fs.get("image_sha256") for fs in filesystems] != digests:
        raise SystemExit("SquashFS reports do not match the compared TRX digests")
if digests[0] != digests[1]:
    timestamps = [report.get("squashfs_created_epoch") for report in (first, second)]
    message = "Matching recorded inputs produced different TRX digests: " + " / ".join(digests)
    if all(type(value) is int and value >= 0 for value in timestamps) and timestamps[0] != timestamps[1]:
        message += f"; SquashFS creation times differ: {timestamps[0]} / {timestamps[1]}"
    section_maps = [report.get("nfqws2_elf_sections_sha256") for report in (first, second)]
    if all(isinstance(sections, dict) and sections for sections in section_maps):
        left, right = section_maps
        changed = sorted(name for name in left.keys() | right.keys()
                         if left.get(name) != right.get(name))
        if changed:
            message += "; nfqws2 ELF sections differ: " + ", ".join(changed)
        else:
            message += "; recorded nfqws2 ELF sections match"
    if filesystems:
        regions = [fs.get("image_regions_sha256") for fs in filesystems]
        if all(isinstance(region, dict) and region for region in regions):
            left, right = regions
            changed = sorted(name for name in left.keys() | right.keys()
                             if left.get(name) != right.get(name))
            message += "; image regions: " + (", ".join(changed) if changed else "match")
        first_files, second_files = (fs.get("squashfs_regular_files_sha256")
                                     for fs in filesystems)
        if not first_files or not second_files:
            raise SystemExit("Missing regular-file inventory in SquashFS reports")
        changed = sorted(name for name in first_files.keys() | second_files.keys()
                         if first_files.get(name) != second_files.get(name))
        message += "; SquashFS regular files: " + (", ".join(changed) if changed else "match")
        metadata = [fs.get("squashfs_metadata_listing_sha256") for fs in filesystems]
        if all(metadata):
            message += "; metadata listings " + ("match" if metadata[0] == metadata[1] else "differ")
    raise SystemExit(message)
print("PASS identical TRX digest for matching recorded inputs: " + digests[0])
