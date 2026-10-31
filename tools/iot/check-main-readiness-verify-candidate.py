#!/usr/bin/env python3
"""Check that an isolated MT7603 candidate binds the main VERIFY producer."""

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidate", type=Path)
    args = parser.parse_args()
    root = args.candidate.resolve(strict=True)
    source = (root / "os/linux/rt_main_dev.c").read_text(encoding="utf-8")
    focused = Path(str(root) + ".manifest.json")
    composition = root.parent / (root.name + "-composition.json")
    manifest = json.loads((focused if focused.exists() else composition).read_text(encoding="utf-8"))

    helper_start = source.index("static int wr_iot_main_readiness_verify(")
    helper_end = source.index("\nint MainVirtualIF_open(", helper_start)
    helper = source[helper_start:helper_end]
    assert helper.count("wr_iot_radio_begin(") == 1
    assert helper.count(",WR_RADIO_VERIFY,&ticket)") == 1
    first_unlock = helper.index("RTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock,flags);")
    observer = helper.index("wr_iot_mt7603_main_config_observed(adapter)")
    second_lock = helper.index("RTMP_IRQ_LOCK(&adapter->wr_iot_transition_lock,flags);", first_unlock)
    owned_finish = helper.index("wr_iot_main_radio_verify_owned(", second_lock)
    assert first_unlock < observer < second_lock < owned_finish
    assert "record->generation==generation" in helper
    assert "WR_REF_FAMILY_MAIN" in helper and "!record->removing" in helper
    assert "wr_iot_registry_count_matches" in helper
    assert "adapter->wr_iot_transition.serial==ticket.serial" in helper
    assert "wr_iot_radio_finish(&adapter->wr_iot_transition,&ticket,0)" in helper

    main_start = source.index("int MainVirtualIF_open(")
    main_end = source.index("\n}\n", main_start) + 2
    main = source[main_start:main_end]
    verify_call = main.index("wr_iot_main_readiness_verify(adapter,net_dev,generation)")
    fail = main.index("if (!owned || !finished)")
    hnat = main.index("RT_MOD_HNAT_REG(net_dev)")
    queue = main.index("netif_start_queue(net_dev)")
    assert fail < verify_call < hnat < queue
    if manifest.get("main_verify_checked_rollback_staged"):
        begin = main.index("wr_iot_main_close_begin_checked(", verify_call)
        preclose = main.index("wr_iot_main_close_preclose_once(", begin)
        down = main.index("wr_iot_main_close_continue_checked(", preclose)
        release = main.index("RT_MOD_DEC_USE_COUNT();", down)
        assert verify_call < begin < preclose < down < release < hnat
        assert "if (closed)\n   RT_MOD_DEC_USE_COUNT();" in main
        if manifest.get("main_recovery_queue_bound"):
            assert "wr_iot_main_verify_recovery_submit(adapter,net_dev,generation," in main
            assert main.index("wr_iot_main_verify_recovery_submit(") > release
        else:
            assert "checked close incomplete, retaining owner" in main
    else:
        assert "recovery owner is still required" in main
    assert manifest["main_readiness_verify_bound"] is True
    assert manifest["production_installed"] is False
    if not manifest.get("main_recovery_queue_bound"):
        assert manifest.get("recovery_owner_bound") is False
    assert manifest["pci_release_gate_bound"] is False
    print("main-readiness VERIFY candidate structure: PASS")
    print("VERIFY lock/readback/revalidation ordering: PASS")
    print("queue/HNAT remain behind verified-open gate: PASS")
    if manifest.get("main_recovery_queue_bound"):
        print("recovery queue staged; PCI release gate remains unbound: CONFIRMED")
    else:
        print("production/recovery/PCI release gates remain unbound: CONFIRMED")


if __name__ == "__main__":
    main()
