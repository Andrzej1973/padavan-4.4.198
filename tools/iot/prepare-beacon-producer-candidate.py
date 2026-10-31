#!/usr/bin/env python3
"""Bind the host beacon producer gate in a new isolated MT7603 tree.

This stage is not a firmware-image or PCI-release acceptance gate. It must be
applied only after the reviewed v41 checked-stop preparation.
"""
import argparse
import hashlib
import json
import shutil
from pathlib import Path


def replace_one(value: str, old: str, new: str, label: str) -> str:
    if value.count(old) != 1 and "\n" in old:
        crlf_old = old.replace("\n", "\r\n")
        if value.count(crlf_old) == 1:
            old = crlf_old
            new = new.replace("\n", "\r\n")
    if value.count(old) != 1:
        raise ValueError(f"{label}: expected one reviewed anchor, found {value.count(old)}")
    return value.replace(old, new, 1)


def edit(output: Path, relative: str, changes: list[tuple[str, str, str]]) -> None:
    path = output / relative
    value = path.read_bytes().decode("latin1")
    for old, new, label in changes:
        value = replace_one(value, old, new, f"{relative} {label}")
    path.write_bytes(value.encode("latin1"))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    source, output = args.source.resolve(strict=True), args.output.resolve()
    if output.exists() or source == output or source in output.parents:
        parser.error("output must be new and outside source")
    if b"wr_iot_mbss_close_checked" not in (source / "ap/ap_mbss_inf.c").read_bytes():
        parser.error("source is not the reviewed v41 checked-stop tree")
    here = Path(__file__).resolve().parent
    shutil.copytree(source, output)
    (output / "include/wr-iot-beacon-producer-gate.h").write_bytes(
        (here / "beacon-producer-gate.h").read_bytes())
    (output / "include/wr-iot-beacon-producer-kernel.h").write_bytes(
        (here / "beacon-producer-kernel.h").read_bytes())

    edit(output, "include/rtmp.h", [
        ('#include "mbss-retirement.h"',
         '#include "mbss-retirement.h"\n#include "wr-iot-beacon-producer-gate.h"', "type"),
        ('wait_queue_head_t wr_iot_ticket_wait;',
         'wait_queue_head_t wr_iot_ticket_wait;\n'
         '\twait_queue_head_t wr_iot_beacon_wait;\n'
         '\tstruct wr_iot_beacon_producer_gate wr_iot_beacon_gates[WDEV_NUM_MAX];',
         "adapter state"),
    ])
    edit(output, "common/rtmp_init.c", [
        ('init_waitqueue_head(&pAd->wr_iot_ticket_wait);',
         'init_waitqueue_head(&pAd->wr_iot_ticket_wait);\n'
         '\t\tinit_waitqueue_head(&pAd->wr_iot_beacon_wait);\n'
         '\t\t{\n\t\t\tUINT wr_iot_gate;\n'
         '\t\t\tfor (wr_iot_gate = 0; wr_iot_gate < WDEV_NUM_MAX; wr_iot_gate++)\n'
         '\t\t\t\twr_iot_beacon_gate_init(&pAd->wr_iot_beacon_gates[wr_iot_gate]);\n'
         '\t\t}', "init"),
    ])

    beacon_wrapper = '''
VOID APUpdateBeaconFrame(RTMP_ADAPTER *pAd, INT apidx)
{
#if defined(MT_MAC) && defined(RTMP_MAC_PCI)
 struct wr_iot_beacon_producer_ticket ticket = {0};
 if (!pAd || apidx < 0 || apidx >= WDEV_NUM_MAX ||
     apidx >= pAd->ApCfg.BssidNum)
  return;
 if (apidx > 0 && pAd->chipCap.hif_type == HIF_MT) {
  if (!wr_iot_bcn_producer_begin(pAd, apidx, &ticket))
   return;
  wr_iot_APUpdateBeaconFrame_inner(pAd, apidx);
  wr_iot_bcn_producer_end(pAd, apidx, &ticket);
  return;
 }
#endif
 wr_iot_APUpdateBeaconFrame_inner(pAd, apidx);
}
'''
    edit(output, "ap/ap_connect.c", [
        ('#include "rt_config.h"',
         '#include "rt_config.h"\n#include "wr-iot-beacon-producer-kernel.h"', "include"),
        ('VOID APUpdateBeaconFrame(RTMP_ADAPTER *pAd, INT apidx)\n{',
         'static VOID wr_iot_APUpdateBeaconFrame_inner(RTMP_ADAPTER *pAd, INT apidx)\n{',
         "beacon inner"),
        ('pMbss->WriteBcnDoneTime[pMbss->timer_loop] = Lowpart;\n\t}\n}',
         'pMbss->WriteBcnDoneTime[pMbss->timer_loop] = Lowpart;\n\t}\n}'
         + beacon_wrapper, "beacon wrapper"),
    ])

    tim_wrapper = '''
VOID APMakeBssTimFrame(RTMP_ADAPTER *pAd, INT apidx)
{
#if defined(MT_MAC) && defined(RTMP_MAC_PCI)
 struct wr_iot_beacon_producer_ticket ticket = {0};
 if (!pAd || apidx < 0 || apidx >= WDEV_NUM_MAX ||
     apidx >= pAd->ApCfg.BssidNum)
  return;
 if (apidx > 0 && pAd->chipCap.hif_type == HIF_MT) {
  if (!wr_iot_bcn_producer_begin(pAd, apidx, &ticket))
   return;
  wr_iot_APMakeBssTimFrame_inner(pAd, apidx);
  wr_iot_bcn_producer_end(pAd, apidx, &ticket);
  return;
 }
#endif
 wr_iot_APMakeBssTimFrame_inner(pAd, apidx);
}
'''
    edit(output, "ap/ap_nps.c", [
        ('#include "rt_config.h"',
         '#include "rt_config.h"\n#include "wr-iot-beacon-producer-kernel.h"', "include"),
        ('VOID APMakeBssTimFrame(RTMP_ADAPTER *pAd, INT apidx)\n{',
         'static VOID wr_iot_APMakeBssTimFrame_inner(RTMP_ADAPTER *pAd, INT apidx)\n{',
         "TIM inner"),
        ('\nVOID APMakeAllTimFrame(RTMP_ADAPTER *pAd)',
         tim_wrapper + '\nVOID APMakeAllTimFrame(RTMP_ADAPTER *pAd)',
         "TIM wrapper"),
    ])

    mbss = output / "ap/ap_mbss.c"
    value = mbss.read_bytes().decode("latin1")
    value = replace_one(value, '#include "rt_config.h"',
                        '#include "rt_config.h"\n#include "wr-iot-beacon-producer-kernel.h"',
                        "MBSS include")
    # Patch function-local slices so a similar assignment in MT hardware-off
    # cannot silently receive the wrong gate operation.
    for name, next_name, changes in (
        ("INT32 MBSS_Open(PNET_DEV pDev)", "INT MBSS_AbortOpen(PNET_DEV pDev)", [
            ('\t\treturn -1;\n\t}\n#ifdef AIRPLAY_SUPPORT',
             '\t\treturn -1;\n\t}\n'
             '\tif (!wr_iot_beacon_gate_open(&pAd->wr_iot_beacon_gates[BssId],\n'
             '\t    pAd->wr_iot_beacon_gates[BssId].generation + 1)) {\n'
             '\t\tRTMP_SEM_UNLOCK(&pAd->BcnRingLock);\n\t\treturn -1;\n'
             '\t}\n#ifdef AIRPLAY_SUPPORT', "open admission"),
        ]),
        ("INT MBSS_AbortOpen(PNET_DEV pDev)", "INT MBSS_Close(PNET_DEV pDev)", [
            ('    RTMP_SEM_LOCK(&pAd->BcnRingLock);\n'
             '    pAd->ApCfg.MBSSID[BssId].bcn_buf.bBcnSntReq = FALSE;\n'
             '    RTMP_SEM_UNLOCK(&pAd->BcnRingLock);',
             '    if (!wr_iot_bcn_revoke_and_drain(pAd, BssId))\n'
             '        return -1;', "abort drain"),
        ]),
        ("INT MBSS_Close(PNET_DEV pDev)", "#endif /* MBSS_SUPPORT */", [
            ('\tpAd->ApCfg.MBSSID[BssId].bcn_buf.bBcnSntReq = FALSE;',
             '\tif (!wr_iot_bcn_revoke_and_drain(pAd, BssId))\n'
             '\t\treturn -1;', "close drain"),
        ]),
    ):
        start = value.index(name)
        end = value.index(next_name, start + len(name))
        fragment = value[start:end]
        for old, new, label in changes:
            fragment = replace_one(fragment, old, new, label)
        value = value[:start] + fragment + value[end:]
    remove_start = value.index("INT MBSS_Remove(RTMP_ADAPTER *pAd)")
    remove_end = value.index("INT32 MBSS_Open(PNET_DEV pDev)", remove_start)
    fragment = value[remove_start:remove_end]
    fragment = replace_one(fragment,
        '        if (pMbss) {\n\t\t\tif (wdev_bcn_buf_deinit',
        '        if (!wr_iot_bcn_remove_ready(pAd, IdBss)) {\n'
        '            wr_iot_mbss_cancel_unmutated(pAd, IdBss, wdev->if_dev);\n'
        '            return NDIS_STATUS_FAILURE;\n'
        '        }\n'
        '        if (pMbss) {\n\t\t\tif (wdev_bcn_buf_deinit', "remove drain gate")
    value = value[:remove_start] + fragment + value[remove_end:]
    mbss.write_bytes(value.encode("latin1"))

    modified = ("include/rtmp.h", "common/rtmp_init.c", "ap/ap_connect.c",
                "ap/ap_nps.c", "ap/ap_mbss.c",
                "include/wr-iot-beacon-producer-gate.h",
                "include/wr-iot-beacon-producer-kernel.h")
    source_files = {p.relative_to(source).as_posix() for p in source.rglob("*")
                    if p.is_file()}
    output_files = {p.relative_to(output).as_posix() for p in output.rglob("*")
                    if p.is_file()}
    added = set(modified) - source_files
    if output_files - source_files != added or source_files - output_files:
        raise RuntimeError("unexpected isolated candidate file set")
    for name in source_files - set(modified):
        if (source / name).read_bytes() != (output / name).read_bytes():
            raise RuntimeError(f"unreviewed candidate change: {name}")
    manifest = {
        "schema": 1, "scope": "isolated beacon/TIM producer gate binding",
        "candidate_files": {name: hashlib.sha256((output / name).read_bytes()).hexdigest()
                            for name in modified},
        "producer_gate_bound": True,
        "recovery_owner_bound": False,
        "pci_release_gate_bound": False,
        "target_compiled": False,
        "production_installed": False,
        "runtime_verified": False,
    }
    Path(str(output) + ".manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
