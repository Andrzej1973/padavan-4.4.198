#!/usr/bin/env python3
"""Bind main ra0 admission in a new isolated MT76x3 candidate tree only."""

import argparse
import shutil
from pathlib import Path


MAIN_OPEN = r'''int MainVirtualIF_open(struct net_device *net_dev)
{
 VOID *pAd = NULL;
 PRTMP_ADAPTER adapter;
 struct wr_iot_radio_ticket ticket;
 struct wr_iot_interface_ref *record;
 unsigned long generation = 0;
 ULONG flags;
 int admitted, retained = 1, owned, finished;

#ifdef IFUP_IN_PROBE
#error "main-open owner candidate requires a separate IFUP_IN_PROBE owner"
#endif
 RT_MOD_INC_USE_COUNT();
 GET_PAD_FROM_NET_DEV(pAd, net_dev);
 if (!pAd) { RT_MOD_DEC_USE_COUNT(); return -1; }
 adapter = (PRTMP_ADAPTER)pAd;
 RTMP_IRQ_LOCK(&adapter->wr_iot_transition_lock, flags);
 admitted = net_dev == adapter->net_dev &&
  wr_iot_main_open_reserve(&adapter->wr_iot_transition,
   adapter->wr_iot_interface_refs, WDEV_NUM_MAX + 1,
   net_dev, VIRTUAL_IF_NUM(adapter), &ticket, &generation);
 RTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock, flags);
 if (!admitted) { RT_MOD_DEC_USE_COUNT(); return -1; }

#ifdef CONFIG_AP_SUPPORT
 RTMP_DRIVER_AP_MAIN_OPEN(pAd);
#endif
 if (VIRTUAL_IF_UP_CLAIM(pAd, net_dev, &ticket, generation) != 0) {
  RTMP_IRQ_LOCK(&adapter->wr_iot_transition_lock, flags);
  record = wr_iot_registry_find(adapter->wr_iot_interface_refs,
   WDEV_NUM_MAX + 1, net_dev, generation);
  if (record)
   wr_iot_ref_complete_main_open(record, net_dev, generation,
    ticket.serial, WR_MAIN_OPEN_UNCERTAIN_FAILURE, &retained);
  wr_iot_radio_finish(&adapter->wr_iot_transition, &ticket, 0);
  RTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock, flags);
  wake_up_all(&adapter->wr_iot_ticket_wait);
  /* AP_MAIN_OPEN already ran: kernel will not call ndo_stop after failure.
   * Retain module pin and record until a checked recovery owner exists. */
  return -1;
 }

 RTMP_IRQ_LOCK(&adapter->wr_iot_transition_lock, flags);
 record = wr_iot_registry_find(adapter->wr_iot_interface_refs,
  WDEV_NUM_MAX + 1, net_dev, generation);
 finished = wr_iot_radio_finish_unverified(
  &adapter->wr_iot_transition, &ticket);
 owned = wr_iot_main_open_accepted(&adapter->wr_iot_transition,
  &ticket, finished) && record && wr_iot_ref_complete_main_open(record,
  net_dev, generation, ticket.serial, WR_MAIN_OPEN_ACQUIRED, &retained);
 if (!owned && record && record->phase == WR_REF_RESERVED)
  wr_iot_ref_complete_main_open(record, net_dev, generation,
   ticket.serial, WR_MAIN_OPEN_UNCERTAIN_FAILURE, &retained);
 RTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock, flags);
 wake_up_all(&adapter->wr_iot_ticket_wait);
 if (!owned || !finished) return -1; /* retain pin; hardware may be open */

#ifdef CONFIG_RA_HW_NAT_WIFI_NEW_ARCH
 RT_MOD_HNAT_REG(net_dev);
#endif
 netif_start_queue(net_dev);
 netif_carrier_on(net_dev);
 netif_wake_queue(net_dev);
 return 0;
}'''


MAIN_DISPATCH = r'''if (claim.operation == WR_RADIO_START ||
                    claim.operation == WR_RADIO_MAIN_OPEN) {
                    valid = wr_iot_virtual_main_open_claim_matches(
                        &claim, &pAd->wr_iot_transition,
                        pAd->wr_iot_interface_refs, WDEV_NUM_MAX + 1,
                        pAd->net_dev, VIRTUAL_IF_NUM(pAd)) &&
                        VIRTUAL_IF_NUM(pAd) != (UINT)~0U;
                    if (valid) {
                        VIRTUAL_IF_INC(pAd);
                        pAd->wr_iot_transition.virtual_up_stage = 1U;
                    }
                    RTMP_IRQ_UNLOCK(&pAd->wr_iot_transition_lock, flags);
                    if (!valid) return NDIS_STATUS_FAILURE;
                    if (claim.operation == WR_RADIO_START) {
                        if (pInfConf->rt28xx_open(pAd->net_dev) != 0) {
                            RTMP_IRQ_LOCK(&pAd->wr_iot_transition_lock, flags);
                            if (pAd->wr_iot_transition.busy == claim.operation &&
                                pAd->wr_iot_transition.serial == claim.serial &&
                                VIRTUAL_IF_NUM(pAd) == 1) {
                                VIRTUAL_IF_DEC(pAd);
                                pAd->wr_iot_transition.virtual_up_stage = 2U;
                            }
                            RTMP_IRQ_UNLOCK(&pAd->wr_iot_transition_lock, flags);
                            return NDIS_STATUS_FAILURE;
                        }
                    } else {
#ifdef CONFIG_AP_SUPPORT
                        extern VOID APMakeAllBssBeacon(IN PRTMP_ADAPTER pAd);
                        extern VOID APUpdateAllBeaconFrame(IN PRTMP_ADAPTER pAd);
                        APMakeAllBssBeacon(pAd);
                        APUpdateAllBeaconFrame(pAd);
#endif
                    }
                    break;
                }
                '''


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    source, output = args.source.resolve(), args.output.resolve()
    if output.exists() or output == source or source in output.parents or output in source.parents:
        parser.error("output must be a new separate directory")
    main_file = source / "os/linux/rt_main_dev.c"
    dispatch_file = source / "common/cmm_cfg.c"
    if not main_file.is_file() or not dispatch_file.is_file():
        parser.error("source is not the isolated virtual-open candidate")
    main_text = main_file.read_text(encoding="utf-8")
    start = main_text.index("int MainVirtualIF_open(struct net_device *net_dev)")
    end = main_text.index("\n}\n", start) + len("\n}")
    original = main_text[start:end]
    if ("VIRTUAL_IF_UP(pAd, net_dev)" not in original or
            "wr_iot_radio_begin(" not in original):
        parser.error("main wrapper has changed; inspect before regeneration")
    dispatch_text = dispatch_file.read_text(encoding="utf-8")
    marker = "valid = claim.operation == WR_RADIO_BSS_OPEN &&"
    if dispatch_text.count(marker) != 1:
        parser.error("claimed dispatcher has changed")
    shutil.copytree(source, output)
    shutil.copyfile(Path(__file__).with_name("radio-transition.h"),
                    output / "include/radio-transition.h")
    (output / "os/linux/rt_main_dev.c").write_text(
        main_text[:start] + MAIN_OPEN + main_text[end:], encoding="utf-8", newline="\n")
    (output / "common/cmm_cfg.c").write_text(
        dispatch_text.replace(marker, MAIN_DISPATCH + marker),
        encoding="utf-8", newline="\n")
    print(f"Prepared isolated main-open owner candidate: {output}")
    print("Legacy family count writers and main close still bypass the owner; do not package.")


if __name__ == "__main__":
    main()
