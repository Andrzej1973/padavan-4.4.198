#!/usr/bin/env python3
"""Bind checked MBSS close to ndo_stop in a new isolated driver tree.

This is a source candidate only. A failed ndo_stop is ignored by Linux 4.4;
the retained close ticket still needs a recovery owner, and PCI teardown
still needs a release gate before this can enter a firmware image.
"""

import argparse
import hashlib
import json
import shutil
from pathlib import Path


LEGACY_START = b"INT MBSS_VirtualIF_Close(PNET_DEV pDev)\n{\n"
LEGACY_END = b'\n#include "wr-iot-mbss-close-checked.inc"'
REPLACEMENT = b"""/* The checked executor is defined below this callback. A failure after
 * admission retains the ticket and module pin. Admission failure retains
 * the open reference without a ticket. Both need an external recovery owner. */
INT wr_iot_mbss_begin_close(PNET_DEV dev, struct wr_iot_radio_ticket *ticket,
                            unsigned long *generation);
INT wr_iot_mbss_close_checked(PNET_DEV dev, unsigned long generation,
                              const struct wr_iot_radio_ticket *ticket);

INT MBSS_VirtualIF_Close(PNET_DEV pDev)
{
    struct wr_iot_radio_ticket ticket;
    unsigned long generation;

    if (wr_iot_mbss_begin_close(pDev, &ticket, &generation) != 0)
        return -1;
    return wr_iot_mbss_close_checked(pDev, generation, &ticket);
}
"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    source = args.source.resolve(strict=True)
    output = args.output.resolve()
    manifest = Path(str(output) + ".manifest.json")
    if output.exists() or manifest.exists():
        parser.error("output directory and manifest path must be new")
    if output == source or source in output.parents:
        parser.error("output must be outside the source tree")
    target = source / "ap" / "ap_mbss_inf.c"
    if b"BOOLEAN wr_iot_mt_radio_off_checked(" not in \
            (source / "hw_ctrl" / "cmm_asic_mt.c").read_bytes():
        parser.error("input is not the reviewed MT7603 checked-off candidate")
    original = target.read_bytes()
    if original.count(LEGACY_START) != 1 or original.count(LEGACY_END) != 1:
        parser.error("reviewed MBSS callback anchors changed")
    start = original.index(LEGACY_START)
    end = original.index(LEGACY_END, start)
    callback = original[start:end]
    for required in (b"CMD_RTPRIV_IOCTL_MBSS_CLOSE", b"VIRTUAL_IF_DOWN",
                     b"RT_MOD_DEC_USE_COUNT", b"return 0;"):
        if callback.count(required) != 1:
            parser.error("reviewed legacy callback changed; re-review before binding")
    checked = (source / "include" / "wr-iot-mbss-close-checked.inc").read_bytes()
    if checked.count(b"INT wr_iot_mbss_begin_close(") != 1 or \
            checked.count(b"INT wr_iot_mbss_close_checked(") != 1:
        parser.error("checked MBSS executor is missing or ambiguous")
    replacement = original[:start] + REPLACEMENT + original[end:]
    if replacement.count(b"INT MBSS_VirtualIF_Close(") != 1:
        parser.error("generated callback is ambiguous")
    shutil.copytree(source, output)
    (output / "ap" / "ap_mbss_inf.c").write_bytes(replacement)
    copied = sorted(p.relative_to(source) for p in source.rglob("*") if p.is_file())
    for relative in copied:
        expected = replacement if relative == Path("ap/ap_mbss_inf.c") else \
            (source / relative).read_bytes()
        if (output / relative).read_bytes() != expected:
            raise RuntimeError(f"unexpected candidate delta: {relative}")
    report = {
        "schema": 1,
        "scope": "isolated MBSS ndo_stop binding only",
        "source_sha256": hashlib.sha256(original).hexdigest(),
        "output_sha256": hashlib.sha256(replacement).hexdigest(),
        "source_files_verified": len(copied),
        "checked_stop_bound": True,
        "admission_failure_recovery_bound": False,
        "recovery_owner_bound": False,
        "pci_release_gate_bound": False,
        "target_compiled": False,
        "production_installed": False,
        "runtime_verified": False,
    }
    manifest.write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
