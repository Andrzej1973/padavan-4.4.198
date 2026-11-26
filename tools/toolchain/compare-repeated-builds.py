#!/usr/bin/env python3
"""Compare provenance reports from two independently executed WR1200JS builds."""
import argparse
import json
import re
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("first", type=Path)
parser.add_argument("second", type=Path)
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
          "readelf_sha256", "kernel_build_metadata", "input_sha256")
differences = [key for key in inputs if not first.get(key) or first[key] != second.get(key)]
if differences:
    raise SystemExit("Build inputs differ or are missing: " + ", ".join(differences))
digests = [report.get("image_sha256", "") for report in (first, second)]
if any(not re.fullmatch(r"[0-9a-f]{64}", digest) for digest in digests):
    raise SystemExit("Missing or invalid TRX SHA-256")
if digests[0] != digests[1]:
    raise SystemExit("Matching recorded inputs produced different TRX digests: " + " / ".join(digests))
print("PASS identical TRX digest for matching recorded inputs: " + digests[0])
