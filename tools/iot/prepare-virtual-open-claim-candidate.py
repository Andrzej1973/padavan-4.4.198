#!/usr/bin/env python3
"""Bind the existing MBSS open ticket through the isolated virtual-UP ABI."""

import argparse
import shutil
from pathlib import Path


def replace_one(path: Path, old: bytes, new: bytes) -> None:
    data = path.read_bytes()
    if data.count(old) != 1:
        raise ValueError(f"{path}: expected one anchor, found {data.count(old)}")
    path.write_bytes(data.replace(old, new))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    source, output = args.source.resolve(), args.output.resolve()
    if not (source / "common/cmm_cfg.c").is_file():
        parser.error("source is not an isolated MT76x3 driver tree")
    if output.exists() or output == source or source in output.parents or output in source.parents:
        parser.error("output must be a new separate directory")
    # Fail before copytree: stale source anchors must not leave another
    # incomplete scratch tree in the shared checkout.
    expected = {
        "include/rtmp_cmd.h": [(b"\tIN\tVOID *if_dev;", 1)],
        "include/rt_os_net.h": [
            (b'#include "chip/chip_id.h"', 1),
            (b"{ rt28xx_open, rt28xx_close, if_dev };", 2),
            (b"__inline VOID VIRTUAL_IF_DOWN(VOID *pAd, VOID *if_dev)", 1),
        ],
        "ap/ap_mbss_inf.c": [
            (b"static INT wr_iot_mbss_open_raw(PNET_DEV pDev)", 1),
            (b"VIRTUAL_IF_UP(pAd, pDev) != 0", 1),
            (b'\t\t\tDBGPRINT(RT_DEBUG_ERROR, ("MBSS open abort failed\\n"));', 1),
        ],
        "ap/ap_mbss.c": [
            (b"/* Inform daemon interface ready */", 1),
            (b"/* Inform daemon interface down */", 1),
        ],
        "include/wr-iot-mbss-open-admission.inc": [
            (b"ret=wr_iot_mbss_open_raw(pDev);", 1),
        ],
        "common/cmm_cfg.c": [
            (b'#include "rt_config.h"', 1),
            (b"RT_CMD_INF_UP_DOWN *pInfConf = (RT_CMD_INF_UP_DOWN *)pData;\r\n"
             b"\t\t\t/* Arithmetic guard only; shared owner must stabilize the count. */", 2),
        ],
        "include/rtmp.h": [(b"wait_queue_head_t wr_iot_registration_wait;", 1)],
        "common/rtmp_init.c": [
            (b"init_waitqueue_head(&pAd->wr_iot_registration_wait);", 1),
        ],
        "os/linux/rt_main_dev.c": [
            (b"static void wr_iot_hold_netdev(const void *device)", 1),
            (b"\tRtmpOSIRQRequest(net_dev);", 1),
            (b"err:\r\n\tRTMP_DRIVER_IRQ_RELEASE(pAd);\r\n\r\n\treturn (-1);", 1),
        ],
    }
    for rel, anchors in expected.items():
        data = (source / rel).read_bytes()
        for anchor, count in anchors:
            if data.count(anchor) != count:
                raise ValueError(f"{rel}: expected {count} source anchors, found {data.count(anchor)}")
    current = Path(__file__).parent
    overlays = {
        "radio-transition.h": "radio-transition.h",
        "interface-reference.h": "interface-reference.h",
        "interface-registry.h": "interface-registry.h",
        "mbss-open-admission.inc": "wr-iot-mbss-open-admission.inc",
        "mbss-close-checked.inc": "wr-iot-mbss-close-checked.inc",
        "virtual-down-checked.inc": "wr-iot-virtual-down.inc",
    }
    for source_name in overlays:
        if not (current / source_name).is_file():
            parser.error(f"missing current candidate fragment: {source_name}")
    if (current / "mbss-open-admission.inc").read_bytes().count(
            b"ret=wr_iot_mbss_open_raw(pDev);") != 1:
        parser.error("current MBSS open fragment has an unexpected raw call")
    shutil.copytree(source, output)
    for source_name, target_name in overlays.items():
        shutil.copyfile(current / source_name, output / "include" / target_name)
    shutil.copyfile(Path(__file__).with_name("virtual-open-claim.h"),
                    output / "include/virtual-open-claim.h")
    shutil.copyfile(Path(__file__).with_name("radio-ticket-wait.inc"),
                    output / "include/wr-iot-radio-ticket-wait.inc")
    replace_one(output / "include/rtmp.h",
                b"wait_queue_head_t wr_iot_registration_wait;",
                b"wait_queue_head_t wr_iot_registration_wait;\n"
                b"\twait_queue_head_t wr_iot_ticket_wait;")
    replace_one(output / "common/rtmp_init.c",
                b"init_waitqueue_head(&pAd->wr_iot_registration_wait);",
                b"init_waitqueue_head(&pAd->wr_iot_registration_wait);\n"
                b"\t\tinit_waitqueue_head(&pAd->wr_iot_ticket_wait);")
    replace_one(output / "os/linux/rt_main_dev.c",
                b"static void wr_iot_hold_netdev(const void *device)",
                b'#include "wr-iot-radio-ticket-wait.inc"\n'
                b"static void wr_iot_hold_netdev(const void *device)")
    main_irq = output / "os/linux/rt_main_dev.c"
    replace_one(main_irq, b"\tRtmpOSIRQRequest(net_dev);",
                b"\tif (RtmpOSIRQRequest(net_dev) != 0)\n"
                b"\t\tgoto err_no_irq;")
    replace_one(main_irq,
                b"err:\r\n\tRTMP_DRIVER_IRQ_RELEASE(pAd);\r\n\r\n\treturn (-1);",
                b"err:\r\n\tRTMP_DRIVER_IRQ_RELEASE(pAd);\r\n"
                b"err_no_irq:\r\n#ifdef WIFI_DIAG\r\n\tDiagProcExit(pAd);\r\n#endif\r\n"
                b"\treturn (-1);")

    request = output / "include/rtmp_cmd.h"
    replace_one(request, b"\tIN\tVOID *if_dev;", b"\tIN\tVOID *if_dev;\n"
                b"\tIN\tunsigned long owner_generation, owner_serial, owner_epoch;\n"
                b"\tIN\tint owner_operation;")
    os_header = output / "include/rt_os_net.h"
    data = os_header.read_bytes()
    if data.count(b'#include "chip/chip_id.h"') != 1:
        raise ValueError("radio header include anchor mismatch")
    data = data.replace(b'#include "chip/chip_id.h"',
                        b'#include "chip/chip_id.h"\n#include "radio-transition.h"')
    if data.count(b"{ rt28xx_open, rt28xx_close, if_dev };") != 2:
        raise ValueError("unexpected virtual request initializers")
    data = data.replace(b"{ rt28xx_open, rt28xx_close, if_dev };",
                        b"{ rt28xx_open, rt28xx_close, if_dev, 0, 0, 0, 0 };")
    anchor = b"__inline VOID VIRTUAL_IF_DOWN(VOID *pAd, VOID *if_dev)"
    if data.count(anchor) != 1:
        raise ValueError("virtual DOWN anchor mismatch")
    claimed = (
        b"/* MBSS supplies its already reserved ticket; never begin another here. */\n"
        b"__inline INT VIRTUAL_IF_UP_CLAIM(VOID *pAd, VOID *if_dev,\n"
        b" const struct wr_iot_radio_ticket *ticket, unsigned long generation)\n"
        b"{\n"
        b" RT_CMD_INF_UP_DOWN InfConf;\n"
        b" if (!ticket || !generation) return -1;\n"
        b" InfConf.rt28xx_open = rt28xx_open;\n"
        b" InfConf.rt28xx_close = rt28xx_close;\n"
        b" InfConf.if_dev = if_dev;\n"
        b" InfConf.owner_generation = generation;\n"
        b" InfConf.owner_serial = ticket->serial;\n"
        b" InfConf.owner_epoch = ticket->epoch;\n"
        b" InfConf.owner_operation = ticket->operation;\n"
        b" return RTMP_COM_IoctlHandle(pAd, NULL, CMD_RTPRIV_IOCTL_VIRTUAL_INF_UP,\n"
        b"   0, &InfConf, 0) == NDIS_STATUS_SUCCESS ? 0 : -1;\n"
        b"}\n\n"
    )
    os_header.write_bytes(data.replace(anchor, claimed + anchor))

    mbss = output / "ap/ap_mbss_inf.c"
    replace_one(mbss, b"static INT wr_iot_mbss_open_raw(PNET_DEV pDev)",
                b"static INT wr_iot_mbss_open_raw(PNET_DEV pDev,\n"
                b" const struct wr_iot_radio_ticket *ticket, unsigned long generation)")
    replace_one(mbss, b"VIRTUAL_IF_UP(pAd, pDev) != 0",
                b"VIRTUAL_IF_UP_CLAIM(pAd, pDev, ticket, generation) != 0")
    replace_one(mbss,
                b'\t\t\tDBGPRINT(RT_DEBUG_ERROR, ("MBSS open abort failed\\n"));',
                b'\t\t{ DBGPRINT(RT_DEBUG_ERROR, ("MBSS open abort failed\\n"));\n'
                b'\t\t  return -2; /* retain module pin: vendor state is uncertain */ }')
    # A secondary BSS does not own band-wide readiness. The main AP lifecycle
    # announces band availability; clearing it here could disable the main BSS.
    mbss_core = output / "ap/ap_mbss.c"
    data = mbss_core.read_bytes()
    for marker, replacement in ((b"/* Inform daemon interface ready */",
                                 b"/* Band readiness belongs to main AP startup. */"),
                                (b"/* Inform daemon interface down */",
                                 b"/* Band readiness belongs to main AP shutdown. */")):
        start = data.rfind(b"#ifdef BAND_STEERING", 0, data.index(marker))
        end = data.index(b"#endif", data.index(marker))
        end += len(b"#endif /* BAND_STEERING */") if data[end:].startswith(b"#endif /* BAND_STEERING */") else len(b"#endif")
        data = data[:start] + replacement + data[end:]
    mbss_core.write_bytes(data)
    admission = output / "include/wr-iot-mbss-open-admission.inc"
    # The vendor tree and local fragments may carry CRLF. Normalize only the
    # isolated output before matching multi-line wakeup anchors.
    for rel in ("include/wr-iot-mbss-open-admission.inc",
                "os/linux/rt_main_dev.c",
                "include/wr-iot-reset-admission.inc"):
        path = output / rel
        path.write_bytes(path.read_bytes().replace(b"\r\n", b"\n"))
    replace_one(admission, b"ret=wr_iot_mbss_open_raw(pDev);",
                b"ret=wr_iot_mbss_open_raw(pDev,&ticket,record->generation);")
    for old, new in (
        (b"  wr_iot_radio_abort_bss_open_unmutated(&adapter->wr_iot_transition,&ticket);\n"
         b"  RTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock,flags);\n  return -1;",
         b"  wr_iot_radio_abort_bss_open_unmutated(&adapter->wr_iot_transition,&ticket);\n"
         b"  RTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock,flags);\n"
         b"  wake_up_all(&adapter->wr_iot_ticket_wait);\n  return -1;"),
        (b"  wr_iot_radio_finish(&adapter->wr_iot_transition,&ticket,0);\n"
         b"  RTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock,flags);\n  return -1;",
         b"  wr_iot_radio_finish(&adapter->wr_iot_transition,&ticket,0);\n"
         b"  RTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock,flags);\n"
         b"  wake_up_all(&adapter->wr_iot_ticket_wait);\n  return -1;"),
        (b" RTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock,flags);\n return ret;",
         b" RTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock,flags);\n"
         b" wake_up_all(&adapter->wr_iot_ticket_wait);\n return ret;"),
    ):
        replace_one(admission, old, new)
    main = output / "os/linux/rt_main_dev.c"
    replace_one(main,
                b"        wr_iot_radio_finish(&adapter->wr_iot_transition, &ticket, 0);\n"
                b"        RTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock, flags);",
                b"        wr_iot_radio_finish(&adapter->wr_iot_transition, &ticket, 0);\n"
                b"        RTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock, flags);\n"
                b"        wake_up_all(&adapter->wr_iot_ticket_wait);")
    replace_one(main,
                b"    wr_iot_radio_finish_unverified(&adapter->wr_iot_transition, &ticket);\n"
                b"    RTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock, flags);",
                b"    wr_iot_radio_finish_unverified(&adapter->wr_iot_transition, &ticket);\n"
                b"    RTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock, flags);\n"
                b"    wake_up_all(&adapter->wr_iot_ticket_wait);")
    reset = output / "include/wr-iot-reset-admission.inc"
    replace_one(reset,
                b" wr_iot_radio_finish_unverified(&pAd->wr_iot_transition,&ticket);\n"
                b" RTMP_IRQ_UNLOCK(&pAd->wr_iot_transition_lock, flags);",
                b" wr_iot_radio_finish_unverified(&pAd->wr_iot_transition,&ticket);\n"
                b" RTMP_IRQ_UNLOCK(&pAd->wr_iot_transition_lock, flags);\n"
                b" wake_up_all(&pAd->wr_iot_ticket_wait);")

    dispatcher = output / "common/cmm_cfg.c"
    replace_one(dispatcher, b'#include "rt_config.h"',
                b'#include "rt_config.h"\n#include "virtual-open-claim.h"')
    anchor = (b"RT_CMD_INF_UP_DOWN *pInfConf = (RT_CMD_INF_UP_DOWN *)pData;\r\n"
              b"\t\t\t/* Arithmetic guard only; shared owner must stabilize the count. */")
    checked = (
        b"RT_CMD_INF_UP_DOWN *pInfConf = (RT_CMD_INF_UP_DOWN *)pData;\n"
        b"\t\t\tif (pInfConf->owner_generation || pInfConf->owner_serial ||\n"
        b"\t\t\t    pInfConf->owner_epoch || pInfConf->owner_operation) {\n"
        b"\t\t\t\tstruct wr_iot_virtual_open_claim claim = {\n"
        b"\t\t\t\t\tpInfConf->if_dev, pInfConf->owner_generation,\n"
        b"\t\t\t\t\tpInfConf->owner_serial, pInfConf->owner_epoch,\n"
        b"\t\t\t\t\tpInfConf->owner_operation};\n"
        b"\t\t\t\tULONG flags;\n"
        b"\t\t\t\tint valid;\n"
        b"\t\t\t\tRTMP_IRQ_LOCK(&pAd->wr_iot_transition_lock, flags);\n"
        b"\t\t\t\tvalid = VIRTUAL_IF_NUM(pAd) > 0 &&\n"
        b"\t\t\t\t\tVIRTUAL_IF_NUM(pAd) != (UINT)~0U &&\n"
        b"\t\t\t\t\t((claim.operation == WR_RADIO_BSS_OPEN &&\n"
        b"\t\t\t\t\t  wr_iot_virtual_open_claim_matches(&claim,\n"
        b"\t\t\t\t\t   &pAd->wr_iot_transition, pAd->wr_iot_interface_refs,\n"
        b"\t\t\t\t\t   WDEV_NUM_MAX + 1)) ||\n"
        b"\t\t\t\t\t (claim.operation == WR_RADIO_AUX_OPEN &&\n"
        b"\t\t\t\t\t  wr_iot_virtual_aux_open_claim_matches(&claim,\n"
        b"\t\t\t\t\t   &pAd->wr_iot_transition, pAd->wr_iot_interface_refs,\n"
        b"\t\t\t\t\t   WDEV_NUM_MAX + 1, pAd->net_dev,\n"
        b"\t\t\t\t\t   VIRTUAL_IF_NUM(pAd))));\n"
        b"\t\t\t\tif (valid) { VIRTUAL_IF_INC(pAd);\n"
        b"\t\t\t\t\tpAd->wr_iot_transition.virtual_up_stage=1U; }\n"
        b"\t\t\t\tRTMP_IRQ_UNLOCK(&pAd->wr_iot_transition_lock, flags);\n"
        b"\t\t\t\tif (!valid) return NDIS_STATUS_FAILURE;\n"
        b"#ifdef CONFIG_AP_SUPPORT\n"
        b"\t\t\t\t{\n"
        b"\t\t\t\t\textern VOID APMakeAllBssBeacon(IN PRTMP_ADAPTER pAd);\n"
        b"\t\t\t\t\textern VOID APUpdateAllBeaconFrame(IN PRTMP_ADAPTER pAd);\n"
        b"\t\t\t\t\tAPMakeAllBssBeacon(pAd);\n"
        b"\t\t\t\t\tAPUpdateAllBeaconFrame(pAd);\n"
        b"\t\t\t\t}\n"
        b"#endif\n"
        b"\t\t\t\tbreak;\n"
        b"\t\t\t}\n"
        b"\t\t\t/* Arithmetic guard only; shared owner must stabilize the count. */"
    )
    data = dispatcher.read_bytes()
    if data.count(anchor) != 2:
        raise ValueError("expected virtual UP and DOWN dispatcher anchors")
    dispatcher.write_bytes(data.replace(anchor, checked, 1))
    print(f"Prepared isolated MBSS/AUX_OPEN virtual-open claim candidate: {output}")
    print("Legacy callers and DOWN still lack one shared owner; do not package.")


if __name__ == "__main__":
    main()
