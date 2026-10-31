#!/usr/bin/env python3
"""Compose checked auxiliary remove results into an isolated MT76x3 overlay.

The input is a partial, nonproduction overlay. Missing headers are read from
the exact pinned source revision; all transformations run in scratch before an
output is published. This does not establish safe PCI adapter release.
"""

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


DRIVER_PREFIX = "trunk/linux-4.4.x/drivers/net/wireless/mediatek/mt76x3/"
HEADERS = ("include/ap_wds.h", "include/ap_apcli.h")


def run(*args: str) -> bytes:
    result = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            check=False)
    if result.returncode:
        raise ValueError(f"command failed ({result.returncode}): {result.stderr.decode(errors='replace')[:400]}")
    return result.stdout


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    inputs = parser.add_mutually_exclusive_group(required=True)
    inputs.add_argument("--source-git", type=Path)
    inputs.add_argument("--source-tree", type=Path, help="Pinned mt76x3 tree; exact header blobs checked")
    args = parser.parse_args()
    source = args.source.resolve(strict=True)
    output = args.output.resolve()
    git_dir = args.source_git.resolve(strict=True) if args.source_git else None
    source_tree = args.source_tree.resolve(strict=True) if args.source_tree else None
    if output.exists() or source in output.parents or output in source.parents:
        parser.error("output must be new and separate from the source")
    manifest_path = source.parent / (source.name + "-composition.json")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("production_installed") is not False or manifest.get("pci_config_observer_staged") is not True:
        parser.error("expected reviewed nonproduction PCI observer source")
    for record in manifest["files"]:
        data = (source / record["path"]).read_bytes()
        if hashlib.sha256(data).hexdigest() != record["sha256"]:
            parser.error("source hash mismatch: " + record["path"])

    script_dir = Path(__file__).resolve().parent
    with tempfile.TemporaryDirectory(prefix="wr-iot-remove-compose-") as scratch:
        scratch_root = Path(scratch)
        base, wds, composed = (scratch_root / name for name in ("base", "wds", "composed"))
        shutil.copytree(source, base)
        for name in HEADERS:
            expected = {"include/ap_wds.h": "12042ef6287754fbb12c26025a65a6c978b97491",
                        "include/ap_apcli.h": "66ef0235eab73243b4e185f6e23d6d57c6ed5fb8"}[name]
            if manifest["source_revision"] != "c25283e915a2a00a763774dd255b14aff997285e":
                raise ValueError("unreviewed source revision")
            blob = ((source_tree / name).read_bytes() if source_tree else
                    run("git", "--git-dir", str(git_dir), "show",
                        manifest["source_revision"] + ":" + DRIVER_PREFIX + name))
            blob_id = hashlib.sha1(b"blob " + str(len(blob)).encode() + b"\0" + blob).hexdigest()
            if blob_id != expected:
                raise ValueError("pinned header blob mismatch: " + name)
            if b"VOID " not in blob:
                raise ValueError("unexpected pinned header: " + name)
            target = base / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(blob)
            manifest["source_git_blobs"][name] = blob_id
        run(sys.executable, str(script_dir / "prepare-wds-remove-result-candidate.py"), str(base), str(wds))
        run(sys.executable, str(script_dir / "prepare-aux-remove-result-candidate.py"), str(wds), str(composed))
        run(sys.executable, str(script_dir / "check-remove-result-abi.py"), str(composed))
        known = {record["path"]: record for record in manifest["files"]}
        for name in HEADERS:
            known[name] = {"path": name, "stage": "checked-aux-remove-result", "purpose": "driver"}
        for name, record in known.items():
            record["sha256"] = hashlib.sha256((composed / name).read_bytes()).hexdigest()
        manifest["files"] = list(known.values())
        manifest["aux_remove_results_staged"] = True
        manifest["pci_release_gate_bound"] = False
        shutil.copytree(composed, output)
    output_manifest = output.parent / (output.name + "-composition.json")
    output_manifest.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Composed {len(manifest['files'])} checked files: {output}")
    print("Release gate remains unbound; this is not production firmware")


if __name__ == "__main__":
    main()
