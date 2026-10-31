#!/usr/bin/env python3
"""Prepare an isolated MT7603 checked radio-off candidate from reviewed v39.

This does not install a driver or claim that MCU ACK proves RF silence.
The output must be a new directory; the reviewed input is never modified.
"""

import argparse
import hashlib
import re
import shutil
from pathlib import Path
from mbss_cr_enable import guard_cr_enable


CHECKED_OFF = r'''/* Checked MT7603 halt path. The CLOSE ticket pins this adapter and excludes
 * concurrent radio writers. An uncertain MCU result is terminal for this
 * attempt: replaying a command whose completion is unknown is not safe. */
BOOLEAN wr_iot_mt_radio_off_checked(RTMP_ADAPTER *pAd,
 const struct wr_iot_radio_ticket *ticket)
{
 WPDMA_GLO_CFG_STRUC cfg;
 ULONG flags;
 UINT32 arb;
 unsigned int stage;
 INT32 bss;
 if (!pAd || !ticket || !pAd->net_dev || !IS_MT7603(pAd) ||
     pAd->chipCap.hif_type != HIF_MT ||
     RTMP_TEST_FLAG(pAd, fRTMP_ADAPTER_NIC_NOT_EXIST) ||
     pAd->iwpriv_command)
  return FALSE;
#ifdef LOAD_FW_ONE_TIME
 /* This build uses an AGG_TEMP write without an MCU result. */
 return FALSE;
#endif
 RTMP_IRQ_LOCK(&pAd->wr_iot_transition_lock, flags);
 if (ticket->operation != WR_RADIO_CLOSE ||
     pAd->wr_iot_transition.busy != WR_RADIO_CLOSE ||
     pAd->wr_iot_transition.serial != ticket->serial) {
  RTMP_IRQ_UNLOCK(&pAd->wr_iot_transition_lock, flags);
  return FALSE;
 }
 stage = pAd->wr_iot_transition.mt_radio_off_stage;
 RTMP_IRQ_UNLOCK(&pAd->wr_iot_transition_lock, flags);
 if (stage == 4U) return TRUE;
 if (stage > 4U) return FALSE;
 if (stage == 0U) {
  RTMP_OS_NETDEV_STOP_QUEUE(pAd->net_dev);
#ifdef CONFIG_AP_SUPPORT
  IF_DEV_CONFIG_OPMODE_ON_AP(pAd) {
   for (bss = FIRST_MBSSID; bss < MAX_MBSSID_NUM(pAd); bss++)
    if (pAd->ApCfg.MBSSID[bss].wdev.if_dev)
     RTMP_OS_NETDEV_STOP_QUEUE(pAd->ApCfg.MBSSID[bss].wdev.if_dev);
  }
#else
  (void)bss;
#endif
  RTMP_SET_FLAG(pAd, fRTMP_ADAPTER_DISABLE_DEQUEUEPACKET);
  if (!AsicSetMacTxRx(pAd, ASIC_MAC_RX, FALSE)) return FALSE;
  RTMP_IO_READ32(pAd, ARB_SCR, &arb);
  if (arb == 0xffffffffU || !(arb & MT_ARB_SCR_RXDIS)) return FALSE;
  RTMP_IRQ_LOCK(&pAd->wr_iot_transition_lock, flags);
  pAd->wr_iot_transition.mt_radio_off_stage = 1U;
  RTMP_IRQ_UNLOCK(&pAd->wr_iot_transition_lock, flags);
  stage = 1U;
 }
 if (stage == 1U) {
  if (!wr_iot_mt_poll_txrx_empty(pAd)) return FALSE;
  RTMP_IRQ_LOCK(&pAd->wr_iot_transition_lock, flags);
  pAd->wr_iot_transition.mt_radio_off_stage = 2U;
  RTMP_IRQ_UNLOCK(&pAd->wr_iot_transition_lock, flags);
  stage = 2U;
 }
 if (stage == 2U) {
  if (RTMP_TEST_FLAG(pAd, fRTMP_ADAPTER_NIC_NOT_EXIST)) return FALSE;
  if (CmdRadioOnOffCtrl(pAd, WIFI_RADIO_OFF) != NDIS_STATUS_SUCCESS) {
   RTMP_IRQ_LOCK(&pAd->wr_iot_transition_lock, flags);
   pAd->wr_iot_transition.mt_radio_off_stage = 5U;
   RTMP_IRQ_UNLOCK(&pAd->wr_iot_transition_lock, flags);
   return FALSE;
  }
  RTMP_IRQ_LOCK(&pAd->wr_iot_transition_lock, flags);
  pAd->wr_iot_transition.mt_radio_off_stage = 3U;
  RTMP_IRQ_UNLOCK(&pAd->wr_iot_transition_lock, flags);
  stage = 3U;
 }
 if (stage == 3U) {
  if (RTMP_TEST_FLAG(pAd, fRTMP_ADAPTER_NIC_NOT_EXIST)) return FALSE;
  /* Keep MAC TX enabled until the MCU radio-off command has completed.
   * AsicSetMacTxRx() reports success without checking the register write. */
  if (!AsicSetMacTxRx(pAd, ASIC_MAC_TXRX, FALSE)) return FALSE;
  RTMP_IO_READ32(pAd, ARB_SCR, &arb);
  if (arb == 0xffffffffU ||
      (arb & (MT_ARB_SCR_TXDIS | MT_ARB_SCR_RXDIS)) !=
       (MT_ARB_SCR_TXDIS | MT_ARB_SCR_RXDIS))
   return FALSE;
  if (!AsicSetWPDMA(pAd, PDMA_TX_RX, FALSE)) return FALSE;
  RTMP_IO_READ32(pAd, MT_WPDMA_GLO_CFG, &cfg.word);
  if (cfg.word == 0xffffffffU || cfg.field.EnableTxDMA ||
      cfg.field.EnableRxDMA || (cfg.word & (TX_DMA_BUSY | RX_DMA_BUSY)))
   return FALSE;
  RTMP_SET_FLAG(pAd, fRTMP_ADAPTER_RADIO_OFF);
  if (RTMP_TEST_FLAG(pAd, fRTMP_ADAPTER_INTERRUPT_ACTIVE))
   RTMP_ASIC_INTERRUPT_DISABLE(pAd);
  RTMP_IRQ_LOCK(&pAd->wr_iot_transition_lock, flags);
  pAd->wr_iot_transition.mt_radio_off_stage = 4U;
  RTMP_IRQ_UNLOCK(&pAd->wr_iot_transition_lock, flags);
 }
 /* MCU command accepted and PDMA disabled/idle. Device runtime observation
  * and callback retirement remain separate release gates. */
 return TRUE;
}
'''


def replace_once(root: Path, name: str, old: str, new: str) -> None:
    path = root / name
    data = path.read_text(encoding="utf-8").replace("\r\n", "\n")
    if data.count(old) != 1:
        raise ValueError(f"Reviewed source anchor changed: {name}")
    path.write_text(data.replace(old, new), encoding="utf-8", newline="\n")


def reject_unclaimed_virtual_up(root: Path) -> None:
    """Retire the count-writing legacy UP path after checking its callers."""
    callers = []
    for path in root.rglob("*"):
        if path.suffix not in (".c", ".h", ".inc"):
            continue
        if path.as_posix().endswith("include/rt_os_net.h"):
            continue  # The unused legacy wrapper definition remains for this stage.
        if re.search(r"\bVIRTUAL_IF_UP\s*\(", path.read_text(encoding="utf-8", errors="replace")):
            callers.append(str(path.relative_to(root)))
    if callers:
        raise ValueError(f"Unclaimed VIRTUAL_IF_UP callers require review: {callers}")
    path = root / "common/cmm_cfg.c"
    data = path.read_text(encoding="utf-8").replace("\r\n", "\n")
    start = "\t\t\t/* Arithmetic guard only; shared owner must stabilize the count. */"
    end = "\n\t\t}\n\t\t\tbreak;\n\n\t\tcase CMD_RTPRIV_IOCTL_VIRTUAL_INF_DOWN:"
    if data.count(start) != 2 or data.count(end) != 1:
        raise ValueError("Reviewed virtual UP/DOWN dispatcher anchors changed")
    up_start = data.index(start)
    up_end = data.index(end, up_start)
    data = (data[:up_start] +
            "\t\t\t/* Every active UP caller must carry a reserved owner ticket. */\n"
            "\t\t\treturn NDIS_STATUS_FAILURE;" + data[up_end:])
    path.write_text(data, encoding="utf-8", newline="\n")


def verify_legacy_virtual_down_inventory(root: Path) -> None:
    """Prevent a new unchecked stop path while the four known ones are retired."""
    expected = {
        "os/linux/rt_main_dev.c": 1,
        "ap/ap_mbss_inf.c": 1,
        "ap/ap_apcli_inf.c": 1,
        "os/linux/rt_profile.c": 1,
    }
    found = {}
    for path in root.rglob("*"):
        if path.suffix not in (".c", ".h", ".inc"):
            continue
        relative = path.relative_to(root).as_posix()
        if relative == "include/rt_os_net.h":
            continue  # This is the legacy wrapper definition, not a caller.
        count = len(re.findall(r"\bVIRTUAL_IF_DOWN\s*\(",
                               path.read_text(encoding="utf-8", errors="replace")))
        if count:
            found[relative] = count
    if found != expected:
        raise ValueError(f"Legacy virtual DOWN callers changed: {found}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    source, output = args.source.resolve(), args.output.resolve()
    allowed_output_root = (Path(__file__).resolve().parents[2] / ".iot-local-check").resolve()
    if allowed_output_root not in output.parents:
        parser.error("output must be a new directory inside .iot-local-check")
    if output.exists() or source == output or source in output.parents:
        parser.error("output must be a new separate directory")
    if not (source / "manifest.json").is_file():
        parser.error("source must be the reviewed isolated v39 candidate")
    shutil.copytree(source, output)
    try:
        # The copied v39 manifest cannot describe modified v40 bytes.
        (output / "manifest.json").unlink()
        here = Path(__file__).resolve().parent
        # v39 is a pinned source snapshot. Apply the reviewed idle-reference
        # provenance gate explicitly; changing the local helper alone would
        # leave the target-compiled v40 copy with the older removal check.
        ref = "include/interface-reference.h"
        replace_once(output, ref,
            " unsigned int published,removing,removal_stage,close_stage;",
            " unsigned int published,removing,removal_stage,close_stage;\n unsigned int open_unmutated;")
        replace_once(output, ref,
            "r->close_stage=0;r->published=0;",
            "r->close_stage=0;r->open_unmutated=0;r->published=0;")
        replace_once(output, ref,
            "r->close_stage=0;r->phase=WR_REF_RESERVED;return 1;",
            "r->close_stage=0;r->open_unmutated=0;r->phase=WR_REF_RESERVED;return 1;")
        replace_once(output, ref,
            "r->phase=acquired?WR_REF_OWNED:WR_REF_IDLE;return 1;",
            "r->phase=acquired?WR_REF_OWNED:WR_REF_IDLE;\n r->open_unmutated=acquired?0U:1U;return 1;")
        replace_once(output, ref,
            "r->phase=WR_REF_IDLE;*retain_pin=0;return 1;",
            "r->phase=WR_REF_IDLE;r->open_unmutated=1;*retain_pin=0;return 1;")
        replace_once(output, ref,
            "r->phase=WR_REF_IDLE;*retain_pin=0;\n }else if(virtual_up_succeeded",
            "r->phase=WR_REF_IDLE;r->open_unmutated=1;*retain_pin=0;\n }else if(virtual_up_succeeded")
        # The checked-close executor is claimed under the adapter lock. The
        # copied v39 header must carry its field before the v40 helper builds.
        replace_once(output, ref,
            "unsigned int published,removing,removal_stage,close_stage;\n unsigned int open_unmutated;",
            "unsigned int published,removing,removal_stage,close_stage,close_running;\n unsigned int open_unmutated;")
        replace_once(output, ref,
            "r->close_stage=0;r->open_unmutated=0;r->published=0;",
            "r->close_stage=0;r->close_running=0;r->open_unmutated=0;r->published=0;")
        replace_once(output, ref,
            "r->close_stage=0;r->open_unmutated=0;r->phase=WR_REF_RESERVED;return 1;",
            "r->close_stage=0;r->close_running=0;r->open_unmutated=0;r->phase=WR_REF_RESERVED;return 1;")
        replace_once(output, "include/wr-iot-netdev-registration.inc",
            "record->phase!=WR_REF_IDLE||pAd->wr_iot_transition.active_tx)",
            "record->phase!=WR_REF_IDLE||pAd->wr_iot_transition.active_tx||\n"
            "    (record->last_token&&!record->open_unmutated&&\n"
            "     record->close_stage!=4U))")
        reviewed_admission_path = source / "include/wr-iot-mbss-open-admission.inc"
        if hashlib.sha256(reviewed_admission_path.read_bytes()).hexdigest() != (
                "642e7a09ea177f5232035e99d115710c35216c188fb061870f5c286661d996c8"):
            raise ValueError("Reviewed v39 MBSS admission changed; re-review before replacement")
        reviewed_admission = reviewed_admission_path.read_text(encoding="utf-8")
        if (reviewed_admission.count("ret=wr_iot_mbss_open_raw(pDev,&ticket,record->generation);") != 1 or
                reviewed_admission.count("wake_up_all(&adapter->wr_iot_ticket_wait);") != 3):
            raise ValueError("Reviewed v39 MBSS claim/wakeup contract changed")
        admission = (here / "mbss-open-admission.inc").read_text(encoding="utf-8")
        if admission.count("ret=wr_iot_mbss_open_raw(pDev);") != 1:
            raise ValueError("Local MBSS raw-open contract changed")
        admission = admission.replace("ret=wr_iot_mbss_open_raw(pDev);",
            "ret=wr_iot_mbss_open_raw(pDev,&ticket,record->generation);", 1)
        for anchor, expected in (
            ("  wr_iot_radio_abort_bss_open_unmutated(&adapter->wr_iot_transition,&ticket);\n  RTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock,flags);\n  return -1;", 1),
            ("  wr_iot_radio_finish(&adapter->wr_iot_transition,&ticket,0);\n  RTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock,flags);\n  return -1;", 2),
            (" RTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock,flags);\n return ret;", 1),
        ):
            if admission.count(anchor) != expected:
                raise ValueError("Local MBSS ticket-retirement wakeup anchor changed")
            admission = admission.replace(anchor,
                anchor.replace("\n  return -1;", "\n  wake_up_all(&adapter->wr_iot_ticket_wait);\n  return -1;")
                      .replace("\n return ret;", "\n wake_up_all(&adapter->wr_iot_ticket_wait);\n return ret;"))
        (output / "include/wr-iot-mbss-open-admission.inc").write_text(admission, encoding="utf-8", newline="\n")
        reviewed_close = source / "include/wr-iot-mbss-close-checked.inc"
        if hashlib.sha256(reviewed_close.read_bytes()).hexdigest() != (
                "c269ee751fcce2ff095bfa5374d33b97fc67d527c241e31d39fac53ba116e65b"):
            raise ValueError("Reviewed v39 MBSS close admission changed; re-review before replacement")
        shutil.copyfile(here / "mbss-close-checked.inc",
                        output / "include/wr-iot-mbss-close-checked.inc")
        for name in ("virtual-open-claim.h", "mt7603-main-observe.h"):
            shutil.copyfile(here / name, output / "include" / name)
        reject_unclaimed_virtual_up(output)
        verify_legacy_virtual_down_inventory(output)
        raw_path = output / "ap/ap_mbss_inf.c"
        raw_path.write_text(guard_cr_enable(raw_path.read_text(encoding="utf-8")),
                            encoding="utf-8", newline="\n")
        replace_once(output, "include/radio-transition.h",
                     "unsigned int joined_workers,shutdown_stage,close_notified,virtual_down_stage,virtual_up_stage;",
                     "unsigned int joined_workers,shutdown_stage,close_notified,virtual_down_stage,virtual_up_stage,mt_radio_off_stage;")
        replace_once(output, "include/radio-transition.h",
                     "s->shutdown_stage=0;s->close_notified=0;s->virtual_down_stage=0;",
                     "s->shutdown_stage=0;s->close_notified=0;s->mt_radio_off_stage=0;s->virtual_down_stage=0;")
        replace_once(output, "include/radio-transition.h",
                     "if(operation==WR_RADIO_START||operation==WR_RADIO_AUX_START){s->joined_workers=0;s->shutdown_stage=0;s->close_notified=0;}",
                     "if(operation==WR_RADIO_START||operation==WR_RADIO_AUX_START){s->joined_workers=0;s->shutdown_stage=0;s->close_notified=0;s->mt_radio_off_stage=0;}")
        replace_once(output, "include/rtmp.h",
                     "INT wr_iot_mgmt_exit_checked(RTMP_ADAPTER *pAd, const struct wr_iot_radio_ticket *ticket);",
                     "INT wr_iot_mgmt_exit_checked(RTMP_ADAPTER *pAd, const struct wr_iot_radio_ticket *ticket);\n#ifdef RTMP_PCI_SUPPORT\nBOOLEAN wr_iot_mt_poll_txrx_empty(RTMP_ADAPTER *pAd);\nBOOLEAN wr_iot_mt_radio_off_checked(RTMP_ADAPTER *pAd, const struct wr_iot_radio_ticket *ticket);\n#endif")
        replace_once(output, "hw_ctrl/cmm_asic_mt.c",
                     "\tRTMP_CLEAR_FLAG(pAd, fRTMP_ADAPTER_POLL_IDLE);\n    return TRUE;\n}\n\nVOID MTPciPollTxRxEmpty",
                     "    /* A disappearance on the final RX read is not an idle receipt. */\n"
                     "    if (RTMP_TEST_FLAG(pAd, fRTMP_ADAPTER_NIC_NOT_EXIST)) {\n"
                     "        RTMP_CLEAR_FLAG(pAd, fRTMP_ADAPTER_POLL_IDLE);\n"
                     "        return FALSE;\n"
                     "    }\n"
                     "\tRTMP_CLEAR_FLAG(pAd, fRTMP_ADAPTER_POLL_IDLE);\n"
                     "    return TRUE;\n}\n\nVOID MTPciPollTxRxEmpty")
        replace_once(output, "hw_ctrl/cmm_asic_mt.c",
                     "}\n#endif\n\n\n#ifdef RTMP_SDIO_SUPPORT\nVOID MTSdioMlmeRadioOff",
                     "}\n\n" + CHECKED_OFF + "#endif\n\n\n#ifdef RTMP_SDIO_SUPPORT\nVOID MTSdioMlmeRadioOff")
        path = output / "common/rtmp_init_inf.c"
        data = path.read_text(encoding="utf-8").replace("\r\n", "\n")
        start = data.index("INT wr_iot_drv_close_checked(")
        tail = data[start:]
        old_wait = ("\tfor (i = 0 ; i < NUM_OF_TX_RING; i++)\n"
                    "\t{\n"
                    "\t\twhile (pAd->DeQueueRunning[i] == TRUE)\n"
                    "\t\t{\n"
                    "\t\t\tDBGPRINT(RT_DEBUG_TRACE, (\"Waiting for TxQueue[%d] done..........\\n\", i));\n"
                    "\t\t\tRtmpusecDelay(1000);\n"
                    "\t\t}\n"
                    "\t}\n")
        new_wait = ("\tfor (i = 0 ; i < NUM_OF_TX_RING; i++)\n"
                    "\t{\n"
                    "\t\tunsigned int waited = 0;\n"
                    "\t\twhile (pAd->DeQueueRunning[i] == TRUE)\n"
                    "\t\t{\n"
                    "\t\t\tif (waited++ >= 1000U) {\n"
                    "\t\t\t\tRTMP_IRQ_LOCK(&pAd->wr_iot_transition_lock,flags);\n"
                    "\t\t\t\tpAd->wr_iot_transition.shutdown_stage = 3U;\n"
                    "\t\t\t\tRTMP_IRQ_UNLOCK(&pAd->wr_iot_transition_lock,flags);\n"
                    "\t\t\t\treturn NDIS_STATUS_FAILURE;\n"
                    "\t\t\t}\n"
                    "\t\t\tRtmpusecDelay(1000);\n"
                    "\t\t}\n"
                    "\t}\n")
        if tail.count(old_wait) != 1:
            raise ValueError("Reviewed checked-close dequeue wait changed")
        tail = tail.replace(old_wait, new_wait, 1)
        old_stage = " if (stage > 2U) return NDIS_STATUS_FAILURE;\n if (stage == 2U) return NDIS_STATUS_SUCCESS;"
        new_stage = (" if (stage > 2U && stage != 4U) return NDIS_STATUS_FAILURE;\n"
                     " if (stage == 2U) return NDIS_STATUS_SUCCESS;\n"
                     "#if defined(RTMP_MAC_PCI) && defined(RTMP_PCI_SUPPORT)\n"
                     " if (stage == 4U) {\n"
                     "  if (pAd->chipCap.hif_type != HIF_MT ||\n"
                     "      (pAd->infType != RTMP_DEV_INF_PCI &&\n"
                     "       pAd->infType != RTMP_DEV_INF_PCIE)) return NDIS_STATUS_FAILURE;\n"
                     "  goto wr_iot_mt_radio_off_resume;\n"
                     " }\n"
                     "#else\n"
                     " if (stage == 4U) return NDIS_STATUS_FAILURE;\n"
                     "#endif")
        if tail.count(old_stage) != 1:
            raise ValueError("Reviewed checked-close stage gate changed")
        tail = tail.replace(old_stage, new_stage, 1)
        anchor = "\t\tif (pAd->infType == RTMP_DEV_INF_PCI || pAd->infType == RTMP_DEV_INF_PCIE)\n\t\t{\n\t\t\tBOOLEAN brc = TRUE;"
        if tail.count(anchor) != 1:
            raise ValueError("Reviewed PCI radio-off entry changed")
        tail = tail.replace(anchor,
            "wr_iot_mt_radio_off_resume:\n" + anchor + "\n"
            "\t\t\tif (pAd->chipCap.hif_type == HIF_MT) {\n"
            "\t\t\t\tRTMP_IRQ_LOCK(&pAd->wr_iot_transition_lock,flags);\n"
            "\t\t\t\tpAd->wr_iot_transition.shutdown_stage=4U;\n"
            "\t\t\t\tRTMP_IRQ_UNLOCK(&pAd->wr_iot_transition_lock,flags);\n"
            "\t\t\t}", 1)
        old = "brc = RT28xxPciAsicRadioOff(pAd, RTMP_HALT, 0);"
        if data[:start].count(old) != 1 or tail.count(old) != 1:
            raise ValueError("Reviewed legacy/checked close split changed")
        tail = tail.replace(old,
            "brc = (pAd->chipCap.hif_type == HIF_MT) ?\n"
            "    wr_iot_mt_radio_off_checked(pAd, ticket) :\n"
            "    RT28xxPciAsicRadioOff(pAd, RTMP_HALT, 0);", 1)
        old_failure = "pAd->wr_iot_transition.shutdown_stage=3U;"
        if tail.count(old_failure) != 1:
            raise ValueError("Reviewed physical-close failure receipt changed")
        tail = tail.replace(old_failure,
            "if (pAd->chipCap.hif_type != HIF_MT)\n"
            "\t\t\t\tpAd->wr_iot_transition.shutdown_stage=3U;", 1)
        data = data[:start] + tail
        path.write_text(data, encoding="utf-8", newline="\n")
    except Exception:
        shutil.rmtree(output)
        raise
    print(f"Prepared isolated MT7603 checked-off candidate: {output}")
    print("No assembly manifest was emitted; re-pin the changed bytes before target compilation.")


if __name__ == "__main__":
    main()
