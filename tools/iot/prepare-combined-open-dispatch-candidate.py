#!/usr/bin/env python3
"""Combine pinned main and auxiliary UP branches in an isolated driver tree."""

import argparse
import hashlib
import shutil
from pathlib import Path


MAIN_SHA256 = "f4cdf1c956fa3560885a269731b282f25a8f2c183dec72cf363004964e86eec8"
OLD_START = b"valid = claim.operation == WR_RADIO_BSS_OPEN &&"
NEW_START = b"valid = VIRTUAL_IF_NUM(pAd) > 0 &&"
END = b"\t\t\t\tif (valid) { VIRTUAL_IF_INC(pAd);"


def branch(data: bytes, marker: bytes) -> bytes:
    if data.count(marker) != 1:
        raise ValueError(f"expected one dispatcher marker, found {data.count(marker)}")
    start = data.index(marker)
    end = data.index(END, start)
    return data[start:end]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("main_candidate", type=Path)
    parser.add_argument("aux_candidate", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    main_dir, aux_dir, output = (p.resolve() for p in
                                  (args.main_candidate, args.aux_candidate, args.output))
    if output.exists() or output in main_dir.parents or output in aux_dir.parents:
        parser.error("output must be a new separate directory")
    main_file = main_dir / "common/cmm_cfg.c"
    aux_file = aux_dir / "common/cmm_cfg.c"
    main_data = main_file.read_bytes()
    if hashlib.sha256(main_data).hexdigest() != MAIN_SHA256:
        parser.error("main candidate dispatcher differs from the reviewed source")
    aux_data = aux_file.read_bytes()
    old = branch(main_data, OLD_START)
    new = branch(aux_data, NEW_START)
    if b"wr_iot_virtual_aux_open_claim_matches" not in new or b"WR_RADIO_AUX_START" in new:
        parser.error("auxiliary branch has an unexpected operation")
    if main_data.count(old) != 1:
        parser.error("main dispatcher branch is ambiguous")
    # Preserve the reviewed START/MAIN_OPEN branch and the rest of v12 exactly.
    shutil.copytree(main_dir, output)
    (output / "common/cmm_cfg.c").write_bytes(main_data.replace(old, new, 1))
    fragments = Path(__file__).resolve().parent
    for source_name, target_name in (
        ("virtual-open-claim.h", "virtual-open-claim.h"),
        ("interface-reference.h", "interface-reference.h"),
        ("interface-registry.h", "interface-registry.h"),
        ("netdev-registration.inc", "wr-iot-netdev-registration.inc"),
    ):
        shutil.copyfile(fragments / source_name, output / "include" / target_name)
    if (output / "common/cmm_cfg.c").read_bytes().count(
            b"wr_iot_virtual_main_open_claim_matches") != 1:
        raise ValueError("main-open branch was lost")
    print(f"Prepared isolated combined open dispatcher: {output}")


if __name__ == "__main__":
    main()
