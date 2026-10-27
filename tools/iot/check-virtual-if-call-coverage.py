#!/usr/bin/env python3
"""Fail closed if MT76x3 virtual-interface caller coverage changes.

Run against a source-pinned staged driver tree, before changing the common
UP/DOWN request ABI. This does not compile or install a driver.
"""

import argparse
import re
from pathlib import Path


EXPECTED = {
    "ap/ap_mbss_inf.c": (1, 1),
    "ap/ap_apcli_inf.c": (1, 1),
    "ap/ap_wds_inf.c": (1, 1),
    "os/linux/rt_main_dev.c": (1, 1),
    "os/linux/rt_profile.c": (1, 1),
}
REGISTRATION = {
    "os/linux/pci_main_dev.c": 1,
    "ap/ap_mbss.c": 1,
    "ap/ap_apcli.c": 1,
    "ap/ap_wds.c": 1,
    "sniffer/sniffer_radiotap.c": 1,
}
CALL = re.compile(r"\bVIRTUAL_IF_(UP|DOWN)\s*\(")
CLAIMED_MBSS_CALL = "VIRTUAL_IF_UP_CLAIM(pAd, pDev, ticket, generation)"
CHECKED_MBSS_INCLUDE = '#include "wr-iot-mbss-close-checked.inc"'


def checked_mbss_stop_coverage(mbss: str, executor: str) -> bool:
    """Require the sole MBSS stop callback to reach the sole checked DOWN."""
    callback = re.search(r"\bINT MBSS_VirtualIF_Close\(PNET_DEV pDev\)\s*\{(.*?)\n\}",
                         mbss, re.S)
    if not callback or mbss.count(CHECKED_MBSS_INCLUDE) != 1:
        return False
    body = callback.group(1)
    return (mbss.count("INT MBSS_VirtualIF_Close(PNET_DEV pDev)") == 1 and
            body.count("wr_iot_mbss_begin_close(pDev, &ticket, &generation)") == 1 and
            body.count("return wr_iot_mbss_close_checked(pDev, generation, &ticket);") == 1 and
            executor.count("INT wr_iot_mbss_close_checked(") == 1 and
            executor.count("wr_iot_virtual_down_checked(ad,ticket)") == 1 and
            not re.search(r"\bVIRTUAL_IF_DOWN\s*\(", body + executor))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("driver", type=Path)
    args = parser.parse_args()
    driver = args.driver.resolve()
    if not (driver / "include/rt_os_net.h").is_file():
        parser.error("expected an MT76x3 driver source root")

    found = {}
    for path in driver.rglob("*.c"):
        rel = path.relative_to(driver).as_posix()
        # Standalone host fixtures define substitutes; only driver callers
        # participate in the kernel ABI transition.
        if path.name.startswith("check-"):
            continue
        source = path.read_text(encoding="utf-8", errors="replace")
        counts = tuple(len(re.findall(r"\bVIRTUAL_IF_" + kind + r"\s*\(", source))
                       for kind in ("UP", "DOWN"))
        if any(counts):
            found[rel] = counts

    mbss = (driver / "ap/ap_mbss_inf.c").read_text(encoding="utf-8", errors="replace")
    claimed = {path.relative_to(driver).as_posix():
               len(re.findall(r"\bVIRTUAL_IF_UP_CLAIM\s*\(",
                              path.read_text(encoding="utf-8", errors="replace")))
               for path in driver.rglob("*.c") if not path.name.startswith("check-")}
    claimed = {path: count for path, count in claimed.items() if count}
    expected = dict(EXPECTED)
    checked_stop = driver / "include/wr-iot-mbss-close-checked.inc"
    checked_binding = ("wr_iot_mbss_begin_close(pDev, &ticket, &generation)" in mbss or
                       "return wr_iot_mbss_close_checked(pDev, generation, &ticket);" in mbss)
    if checked_binding:
        if not checked_stop.is_file() or not checked_mbss_stop_coverage(
                mbss, checked_stop.read_text(encoding="utf-8", errors="replace")):
            print("Checked MBSS stop lost its callback or sole DOWN executor")
            return 1
        expected["ap/ap_mbss_inf.c"] = (1, 0)
    if claimed:
        allowed = ({"ap/ap_mbss_inf.c": 1},
                   {"ap/ap_mbss_inf.c": 1, "os/linux/rt_main_dev.c": 1},
                   {"ap/ap_mbss_inf.c": 1, "ap/ap_wds_inf.c": 1,
                    "os/linux/rt_main_dev.c": 1},
                   {"ap/ap_mbss_inf.c": 1, "ap/ap_wds_inf.c": 1,
                    "ap/ap_apcli_inf.c": 1, "os/linux/rt_main_dev.c": 1},
                   {"ap/ap_mbss_inf.c": 1, "ap/ap_wds_inf.c": 1,
                    "ap/ap_apcli_inf.c": 1, "os/linux/rt_main_dev.c": 1,
                    "os/linux/rt_profile.c": 1})
        if claimed not in allowed or mbss.count(CLAIMED_MBSS_CALL) != 1:
            print("Claimed virtual-UP caller coverage changed:", claimed)
            return 1
        expected["ap/ap_mbss_inf.c"] = (0, 0 if checked_binding else 1)
        if "ap/ap_wds_inf.c" in claimed:
            expected["ap/ap_wds_inf.c"] = (0, 1)
            wds = (driver / "ap/ap_wds_inf.c").read_text(
                encoding="utf-8", errors="replace")
            wds_open = wds[wds.index("INT WdsVirtualIF_open("):
                           wds.index("INT WdsVirtualIF_close(")]
            after_up = wds_open[wds_open.index("VIRTUAL_IF_UP_CLAIM("):]
            if (wds_open.count("wr_iot_aux_open_reserve(") != 1 or
                    "WR_REF_FAMILY_WDS" not in wds_open or
                    "VIRTUAL_IF_NUM(adapter)>0" not in wds_open or
                    wds_open.count("wr_iot_aux_open_accepted(") != 1 or
                    "wr_iot_ref_complete_aux_open(" not in after_up or
                    "RT_MOD_DEC_USE_COUNT();" in after_up):
                print("WDS claimed open lost its admission/failure fence")
                return 1
            remove = re.search(r"^(?:VOID|INT) RT28xx_WDS_Remove\(", wds, re.M)
            if not remove:
                print("WDS remove signature changed")
                return 1
            wds_close = wds[wds.index("INT WdsVirtualIF_close("):
                            remove.start()]
            if "wr_iot_aux_close_reserve(" in wds_close:
                expected["ap/ap_wds_inf.c"] = (0, 0)
                first_close, _, retry_close = wds_close.partition(
                    "INT WdsVirtualIF_close_retry(")
                after_down = first_close[first_close.index("wr_iot_virtual_down_checked("):]
                if (first_close.count("wr_iot_aux_close_reserve(") != 1 or
                        first_close.count("wr_iot_virtual_down_checked(") != 1 or
                        "WR_REF_FAMILY_WDS" not in first_close or
                        "if(ret!=NDIS_STATUS_SUCCESS)return -1;" not in after_down or
                        not any(marker in after_down for marker in
                                ("wr_iot_aux_close_finalize_after_down(",
                                 "wr_iot_ref_consume(")) or
                        "RT_MOD_DEC_USE_COUNT();" not in after_down):
                    print("WDS checked close lost its admission/result fence")
                    return 1
                retry_body, _, complete_body = retry_close.partition(
                    "INT WdsVirtualIF_close_complete(")
                if retry_close and (
                        retry_body.count("wr_iot_aux_close_retry_unmutated_down(") != 1 or
                        retry_body.count("wr_iot_aux_close_retry_release(") != 1 or
                        retry_body.count("wr_iot_virtual_down_checked(") != 1 or
                        not any(marker in retry_body for marker in
                                ("wr_iot_aux_close_finalize_after_down(",
                                 "wr_iot_ref_consume(")) or
                        retry_body.count("RT_MOD_DEC_USE_COUNT();") != 1 or
                        "RTMP_OS_NETDEV_STOP_QUEUE(" in retry_body or
                        "RT_MOD_HNAT_DEREG(" in retry_body):
                    print("WDS retained retry lost its same-ticket fence")
                    return 1
                if complete_body and (
                        complete_body.count("wr_iot_aux_close_claim_after_down(") != 1 or
                        complete_body.count("wr_iot_aux_close_finalize_after_down(") != 1 or
                        "wr_iot_virtual_down_checked(" in complete_body or
                        "RTMP_OS_NETDEV_STOP_QUEUE(" in complete_body or
                        "RT_MOD_HNAT_DEREG(" in complete_body):
                    print("WDS post-DOWN completion repeats vendor work")
                    return 1
        if "ap/ap_apcli_inf.c" in claimed:
            expected["ap/ap_apcli_inf.c"] = (0, 1)
            apcli = (driver / "ap/ap_apcli_inf.c").read_text(
                encoding="utf-8", errors="replace")
            apcli_open = apcli[apcli.index("INT ApCli_VirtualIF_Open("):
                               apcli.index("INT ApCli_VirtualIF_Close(")]
            after_up = apcli_open[apcli_open.index("VIRTUAL_IF_UP_CLAIM("):]
            if (apcli_open.count("wr_iot_aux_open_reserve(") != 1 or
                    "WR_REF_FAMILY_APCLI" not in apcli_open or
                    "VIRTUAL_IF_NUM(adapter)>0" not in apcli_open or
                    apcli_open.count("wr_iot_aux_open_accepted(") != 1 or
                    "CMD_RTPRIV_IOCTL_APC_OPEN" not in after_up or
                    "wr_iot_ref_complete_aux_open(" not in after_up or
                    "RT_MOD_DEC_USE_COUNT();" in after_up):
                print("AP-client claimed open lost its admission/result fence")
                return 1
        if "os/linux/rt_profile.c" in claimed:
            expected["os/linux/rt_profile.c"] = (0, 1)
            profile = (driver / "os/linux/rt_profile.c").read_text(
                encoding="utf-8", errors="replace")
            monitor_open = profile[profile.index("INT Monitor_VirtualIF_Open("):
                                   profile.index("INT Monitor_VirtualIF_Close(")]
            after_up = monitor_open[monitor_open.index("VIRTUAL_IF_UP_CLAIM("):]
            sniffer = (driver / "sniffer/sniffer_radiotap.c").read_text(
                encoding="utf-8", errors="replace")
            identity = sniffer[sniffer.index("BOOLEAN Monitor_Open("):
                               sniffer.index("BOOLEAN Monitor_Close(")]
            if (monitor_open.count("wr_iot_aux_open_reserve(") != 1 or
                    "WR_REF_FAMILY_MONITOR" not in monitor_open or
                    "VIRTUAL_IF_NUM(adapter)>0" not in monitor_open or
                    monitor_open.count("wr_iot_aux_open_accepted(") != 1 or
                    "CMD_RTPRIV_IOCTL_SNIFF_OPEN" not in after_up or
                    "wr_iot_ref_complete_aux_open(" not in after_up or
                    "RT_MOD_DEC_USE_COUNT();" in after_up or
                    "return FALSE;" not in identity):
                print("monitor claimed open lost its identity/result fence")
                return 1
        if "os/linux/rt_main_dev.c" in claimed:
            expected["os/linux/rt_main_dev.c"] = (0, 1)
            main_claim = (driver / "os/linux/rt_main_dev.c").read_text(
                encoding="utf-8", errors="replace")
            main_start = main_claim.index("int MainVirtualIF_open(")
            main_open = main_claim[main_start:
                                   main_claim.index("int rt28xx_close(", main_start)]
            after_claim = main_open[main_open.index("if (VIRTUAL_IF_UP_CLAIM("):]
            if (main_open.count("wr_iot_main_open_reserve(") != 1 or
                    main_open.index("wr_iot_main_open_reserve(") >
                    main_open.index("RTMP_DRIVER_AP_MAIN_OPEN(pAd);") or
                    "WR_MAIN_OPEN_UNCERTAIN_FAILURE" not in after_claim or
                    "wr_iot_main_open_accepted(" not in after_claim or
                    "RT_MOD_DEC_USE_COUNT();" in after_claim or
                    "#error \"main-open owner candidate" not in main_open):
                print("main claimed open lost its reservation/failure fence")
                return 1
            common = (driver / "common/cmm_cfg.c").read_text(
                encoding="utf-8", errors="replace")
            claimed_up = common[common.index("case CMD_RTPRIV_IOCTL_VIRTUAL_INF_UP:"):
                                common.index("case CMD_RTPRIV_IOCTL_VIRTUAL_INF_DOWN:")]
            if ("wr_iot_virtual_main_open_claim_matches(" not in claimed_up or
                    "claim.operation == WR_RADIO_START" not in claimed_up or
                    "pInfConf->rt28xx_open(pAd->net_dev)" not in claimed_up):
                print("main claimed dispatcher path missing")
                return 1
        header = (driver / "include/rt_os_net.h").read_text(encoding="utf-8", errors="replace")
        if header.count("__inline INT VIRTUAL_IF_UP_CLAIM(") != 1:
            print("Claimed virtual-UP request helper missing")
            return 1
        raw_abort = mbss[mbss.index("CMD_RTPRIV_IOCTL_MBSS_ABORT_OPEN"):]
        if (raw_abort.count("return -2; /* retain module pin: vendor state is uncertain */") != 1 or
                raw_abort.index("return -2; /* retain module pin: vendor state is uncertain */") >
                raw_abort.index("RT_MOD_DEC_USE_COUNT();")):
            print("Failed MBSS abort no longer retains uncertain resources")
            return 1
        admission = (driver / "include/wr-iot-mbss-open-admission.inc").read_text(
            encoding="utf-8", errors="replace")
        acquired_failure = "if(ret==-3){" in admission
        uncertain_calls = 2 if acquired_failure else 1
        if (admission.count("if(ret==-2){") != 1 or
                admission.count("wr_iot_ref_open_uncertain(") != uncertain_calls):
            print("MBSS uncertain-open owner handoff missing")
            return 1
        if acquired_failure:
            acquired_branch = admission[admission.index("if(ret==-3){"):
                                        admission.index("if(ret==-2){")]
            if ("wr_iot_ref_open_finish(record,pDev,record->generation,ticket.serial,1)"
                    not in acquired_branch or
                    "wr_iot_radio_finish(&adapter->wr_iot_transition,&ticket,0)"
                    not in acquired_branch or
                    "RT_MOD_DEC_USE_COUNT();" in acquired_branch or
                    "return -3;" not in mbss):
                print("MBSS acquired post-UP failure owner handoff missing")
                return 1
        core = (driver / "ap/ap_mbss.c").read_text(encoding="utf-8", errors="replace")
        mbss_open = core[core.index("INT32 MBSS_Open("):core.index("INT MBSS_AbortOpen(")]
        abort = core[core.index("INT MBSS_AbortOpen("):core.index("INT MBSS_Close(")]
        mbss_close = core[core.index("INT MBSS_Close("):]
        if any("BndStrg_SetInfFlags(" in section for section in
               (mbss_open, abort, mbss_close)):
            print("secondary MBSS must not publish band-wide Band Steering readiness")
            return 1
        if (driver / "include/wr-iot-radio-ticket-wait.inc").exists():
            wake_paths = {
                "include/wr-iot-mbss-open-admission.inc":
                    4 if acquired_failure else 3,
                "include/wr-iot-reset-admission.inc": 1,
                "os/linux/rt_main_dev.c": 2,
            }
            for rel, count in wake_paths.items():
                source = (driver / rel).read_text(encoding="utf-8", errors="replace")
                if (source.count("wake_up_all(&") < count or
                        source.count("wr_iot_ticket_wait);") != count):
                    print("radio ticket retirement wakeup coverage changed:", rel)
                    return 1
            adapter = (driver / "include/rtmp.h").read_text(encoding="utf-8", errors="replace")
            init = (driver / "common/rtmp_init.c").read_text(encoding="utf-8", errors="replace")
            if (adapter.count("wait_queue_head_t wr_iot_ticket_wait;") != 1 or
                    init.count("init_waitqueue_head(&pAd->wr_iot_ticket_wait);") != 1):
                print("radio ticket wait queue storage or initialization missing")
                return 1
        main_source = (driver / "os/linux/rt_main_dev.c").read_text(
            encoding="utf-8", errors="replace")
        if "err_no_irq:" in main_source:
            physical_open = main_source[main_source.index("int rt28xx_open("):
                                         main_source.index("PNET_DEV RtmpPhyNetDevInit(")]
            if (physical_open.count("if (RtmpOSIRQRequest(net_dev) != 0)") != 1 or
                    physical_open.count("goto err_no_irq;") != 1 or
                    physical_open.count("RTMP_DRIVER_IRQ_RELEASE(pAd);") != 1 or
                    physical_open.index("RTMP_DRIVER_IRQ_RELEASE(pAd);") >
                    physical_open.index("err_no_irq:")):
                print("physical first-open IRQ failure path changed")
                return 1
    expected = {path: counts for path, counts in expected.items() if any(counts)}
    if found != expected:
        print("Virtual-interface caller coverage changed:")
        print("expected:", expected)
        print("found:   ", found)
        return 1

    registration = {}
    for rel, expected_count in REGISTRATION.items():
        path = driver / rel
        if not path.is_file():
            print(f"Registration path missing: {rel}")
            return 1
        source = path.read_text(encoding="utf-8", errors="replace")
        count = len(re.findall(r"\bwr_iot_netdev_attach_checked\s*\(", source))
        registration[rel] = count
        if count != expected_count:
            print(f"Registration path changed: {rel}: expected {expected_count}, found {count}")
            return 1

    request = (driver / "include/rtmp_cmd.h").read_text(encoding="utf-8", errors="replace")
    match = re.search(r"typedef struct __RT_CMD_INF_UP_DOWN\s*\{(.*?)\}\s*RT_CMD_INF_UP_DOWN;",
                      request, re.S)
    if not match:
        print("RT_CMD_INF_UP_DOWN definition missing or changed")
        return 1

    print("Verified five MT76x3 caller families, including isolated MBSS claim when present.")
    print("Verified five netdev registration paths use checked attach.")
    print("Request fields (audit only):", " ".join(match.group(1).split()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
