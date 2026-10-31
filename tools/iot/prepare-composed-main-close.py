#!/usr/bin/env python3
"""Place reviewed partial main ndo_stop into a separate IoT driver candidate."""

import argparse
import hashlib
import json
import shutil
from pathlib import Path


def function(source: str, signature: str) -> str:
    if source.count(signature) != 1:
        raise ValueError("ambiguous function: " + signature)
    start = source.index(signature)
    opening = source.index("{", start)
    depth, end = 1, opening + 1
    while depth:
        if end >= len(source):
            raise ValueError("unterminated function: " + signature)
        depth += (source[end] == "{") - (source[end] == "}")
        end += 1
    return source[start:end]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    source, output = args.source.resolve(strict=True), args.output.resolve()
    if output.exists() or source == output or source in output.parents or output in source.parents:
        parser.error("output must be new and separate")
    manifest = json.loads((source.parent / (source.name + "-composition.json")).read_text(encoding="utf-8"))
    if manifest.get("production_installed") is not False or \
            manifest.get("complete_driver_tree") is not False or \
            manifest.get("mt7603_checked_radio_off_composed") is not True:
        parser.error("input is not the reviewed partial radio-off bundle")
    for record in manifest["files"]:
        path = source / record["path"]
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != record["sha256"]:
            parser.error("input changed: " + record["path"])
    name = "os/linux/rt_main_dev.c"
    original = (source / name).read_text(encoding="utf-8")
    signature = "int MainVirtualIF_close(IN struct net_device *net_dev)"
    old = function(original, signature)
    if any(old.count(token) != 1 for token in
           ("wr_iot_radio_main_down", "RTMPInfClose(pAd)", "VIRTUAL_IF_DOWN(pAd)",
            "RT_MOD_DEC_USE_COUNT()")):
        parser.error("main close baseline changed")
    reviewed = Path(__file__).with_name("main-close-checked.inc").read_text(encoding="utf-8")
    signatures = (
        "static int wr_iot_main_close_continue_checked(",
        "static int wr_iot_main_close_begin_checked(",
        "static int wr_iot_main_close_preclose_once(",
    )
    if any(signature in original for signature in signatures):
        parser.error("shared close helpers already present")
    helper, begin, preclose = (function(reviewed, signature)
                               for signature in signatures)
    new = function(reviewed, signature)
    worker_signature = "static int wr_iot_main_recovery_execute("
    if worker_signature in original:
        parser.error("deferred close executor already present")
    worker = function(reviewed, worker_signature)
    if any(new.count(token) != 1 for token in
           ("wr_iot_main_close_begin_checked", "wr_iot_main_close_preclose_once",
            "wr_iot_main_close_continue_checked", "RT_MOD_DEC_USE_COUNT()")):
        parser.error("reviewed main close changed")
    if any(begin.count(token) != 1 for token in
           ("wr_iot_main_stop_request", "wr_iot_ref_begin_close",
            "wr_iot_main_close_claim_preclose")) or \
            any(preclose.count(token) != 1 for token in
                ("RTMPInfClose", "wr_iot_main_close_claim_void_preclose",
                 "wr_iot_main_close_finish_preclose")):
        parser.error("shared close admission or preclose changed")
    if any(helper.count(token) != 1 for token in
           ("wr_iot_main_close_receipt_matches", "wr_iot_virtual_down_checked",
            "wr_iot_main_stop_complete")):
        parser.error("shared close continuation changed")
    if any(worker.count(token) != 1 for token in
           ("wr_iot_main_recovery_begin", "wr_iot_main_recovery_bind_close",
            "wr_iot_main_recovery_mark_completed", "wr_iot_main_recovery_retain",
            "wr_iot_main_close_continue_checked")):
        parser.error("deferred close executor changed")
    if "#include \"wr-iot-physical-close-result.inc\"" not in original or \
            "INT wr_iot_virtual_down_checked(" not in \
            (source / "include/wr-iot-virtual-down.inc").read_text(encoding="utf-8"):
        parser.error("checked close chain is incomplete")
    header_name = "include/main-stop-owned.h"
    header_before = (source / header_name).read_text(encoding="utf-8")
    if "wr_iot_main_close_claim_preclose" not in header_before:
        parser.error("main stop header baseline changed")
    header_after = Path(__file__).with_name("main-stop-owned.h").read_text(encoding="utf-8")
    if "wr_iot_main_close_claim_void_preclose" in header_before and header_before != header_after:
        parser.error("already-staged main stop header differs from reviewed helper")
    if header_after.count("wr_iot_main_close_claim_void_preclose") != 1:
        parser.error("reviewed one-shot preclose gate missing")
    owner_header_name = "include/main-open-recovery-owner.h"
    owner_before = (source / owner_header_name).read_text(encoding="utf-8")
    if "wr_iot_main_recovery_bind_close" not in owner_before:
        parser.error("recovery owner header baseline changed")
    owner_after = Path(__file__).with_name("main-open-recovery-owner.h").read_text(encoding="utf-8")
    if "wr_iot_main_recovery_preclose_uncertain" in owner_before and owner_before != owner_after:
        parser.error("already-staged recovery owner differs from reviewed helper")
    if owner_after.count("wr_iot_main_recovery_preclose_uncertain") != 1:
        parser.error("reviewed recovery owner missing")
    shutil.copytree(source, output)
    (output / name).write_text(original.replace(
        old, helper + "\n\n" + begin + "\n\n" + preclose + "\n\n" +
        new + "\n\n" + worker, 1),
                               encoding="utf-8", newline="\n")
    (output / header_name).write_text(header_after, encoding="utf-8", newline="\n")
    (output / owner_header_name).write_text(owner_after, encoding="utf-8", newline="\n")
    for record in manifest["files"]:
        if record["path"] in (name, header_name, owner_header_name):
            record["stage"] += "+main-close-partial"
            record["sha256"] = hashlib.sha256((output / record["path"]).read_bytes()).hexdigest()
    manifest["main_close_partial_composed"] = True
    manifest["main_close_void_preclose_once_staged"] = True
    manifest["main_close_deferred_executor_staged"] = True
    manifest["main_close_recovery_bound"] = False
    manifest["pci_release_gate_bound"] = False
    manifest["complete_driver_tree"] = False
    manifest["production_installed"] = False
    (output.parent / (output.name + "-composition.json")).write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print("PASS partial main close composition; recovery and PCI release remain unbound")


if __name__ == "__main__":
    main()
