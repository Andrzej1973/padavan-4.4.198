#!/usr/bin/env python3
"""Prepare an isolated v42+ MBSS family preflight source candidate.

The work-joined receipt is intentionally initialized false and not produced
here. This candidate must not enter an ordinary firmware image before the
PCI close/join/terminal owner is implemented and tested.
"""
import argparse
import hashlib
import json
import shutil
from pathlib import Path


def replace_once(path: Path, old: bytes, new: bytes) -> None:
    data = path.read_bytes()
    if data.count(old) != 1:
        raise SystemExit(f"reviewed anchor changed: {path}: {old[:60]!r}")
    path.write_bytes(data.replace(old, new, 1))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    source = args.source.resolve(strict=True)
    output = args.output.resolve()
    if output.exists() or output == source or source in output.parents:
        parser.error("output must be new and outside the source tree")
    if b"wr_iot_mbss_close_checked" not in (source / "ap/ap_mbss_inf.c").read_bytes():
        parser.error("source lacks the reviewed checked MBSS close")
    if b"wr_iot_beacon_gates" not in (source / "include/rtmp.h").read_bytes():
        parser.error("source is not the reviewed v42 beacon candidate")
    here = Path(__file__).resolve().parent
    shutil.copytree(source, output)
    shutil.copyfile(here / "mbss-close-evidence.h",
                    output / "include/mbss-close-evidence.h")
    shutil.copyfile(here / "mbss-global-preflight.inc",
                    output / "include/wr-iot-mbss-global-preflight.inc")
    replace_once(output / "include/rtmp.h",
                 b'#include "interface-registry.h"',
                 b'#include "interface-registry.h"\n#include "mbss-close-evidence.h"')
    replace_once(output / "include/rtmp.h",
                 b'unsigned int wr_iot_registration_inflight;',
                 b'unsigned int wr_iot_registration_inflight;\n'
                 b'\tunsigned int wr_iot_pci_work_joined;\n'
                 b'\tunsigned int wr_iot_mbss_construction_active;')
    replace_once(output / "common/rtmp_init.c",
                 b'init_waitqueue_head(&pAd->wr_iot_ticket_wait);',
                 b'init_waitqueue_head(&pAd->wr_iot_ticket_wait);\n'
                 b'\t\tpAd->wr_iot_pci_work_joined = 0;\n'
                 b'\t\tpAd->wr_iot_mbss_construction_active = 0;')
    replace_once(output / "ap/ap_mbss.c",
                 b'#include "wr-iot-beacon-producer-kernel.h"',
                 b'#include "wr-iot-beacon-producer-kernel.h"\n'
                 b'#include "wr-iot-mbss-global-preflight.inc"')
    replace_once(output / "ap/ap_mbss.c",
                 b'\t/* sanity check to avoid redundant virtual interfaces are created */\n'
                 b'\tif (pAd->FlgMbssInit != FALSE)\n\t\treturn;',
                 b'\t/* Cover the pre-registration wdev.if_dev construction window. */\n'
                 b'\tif (wr_iot_mbss_construction_begin(pAd) != NDIS_STATUS_SUCCESS)\n'
                 b'\t\treturn;')
    replace_once(output / "ap/ap_mbss.c",
                 b'\t\t\tDBGPRINT(RT_DEBUG_ERROR, ("%s():func_dev is NULL!\\n", __FUNCTION__));\n'
                 b'\t\t\treturn;',
                 b'\t\t\tDBGPRINT(RT_DEBUG_ERROR, ("%s():func_dev is NULL!\\n", __FUNCTION__));\n'
                 b'\t\t\tgoto wr_iot_construct_done;')
    replace_once(output / "ap/ap_mbss.c",
                 b'\tpAd->FlgMbssInit = TRUE;\n\n}',
                 b'\tpAd->FlgMbssInit = TRUE;\n'
                 b'wr_iot_construct_done:\n'
                 b'\twr_iot_mbss_construction_end(pAd);\n}')
    replace_once(output / "ap/ap_mbss.c",
                 b'INT MBSS_Remove(RTMP_ADAPTER *pAd)\n{\n\tstruct wifi_dev *wdev;\n'
                 b'\tUINT IdBss;\n    BSS_STRUCT *pMbss;\n',
                 b'INT MBSS_Remove(RTMP_ADAPTER *pAd)\n{\n\tstruct wifi_dev *wdev;\n'
                 b'\tUINT IdBss;\n    BSS_STRUCT *pMbss;\n'
                 b'\tif (wr_iot_mbss_global_preflight(pAd) != NDIS_STATUS_SUCCESS)\n'
                 b'\t\treturn NDIS_STATUS_FAILURE;\n')
    changed = ("include/rtmp.h", "common/rtmp_init.c", "ap/ap_mbss.c",
               "include/mbss-close-evidence.h",
               "include/wr-iot-mbss-global-preflight.inc")
    manifest = {"source": str(source), "candidate": str(output),
                "production_installed": False, "pci_owner_bound": False,
                "files": {name: hashlib.sha256((output / name).read_bytes()).hexdigest()
                          for name in changed}}
    Path(str(output) + ".manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print("Prepared MBSS global preflight candidate; PCI owner remains unbound")


if __name__ == "__main__":
    main()
