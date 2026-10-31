#!/usr/bin/env python3
"""Extract the isolated WDS ndo_stop body into a host result fixture."""

import argparse
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("driver", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output must be a new file")
    source = (args.driver / "ap/ap_wds_inf.c").read_text(encoding="utf-8")
    start = "INT WdsVirtualIF_close("
    ends = [x for x in ("VOID RT28xx_WDS_Remove(", "INT RT28xx_WDS_Remove(") if source.count(x) == 1]
    if len(ends) != 1:
        parser.error("ambiguous WDS remove result ABI")
    end = ends[0]
    if source.count(start) != 1 or source.count(end) != 1:
        parser.error("WDS close wrapper anchors changed")
    body = source[source.index(start):source.index(end)]
    required = ("wr_iot_aux_close_reserve(",
                "wr_iot_aux_close_retry_unmutated_down(",
                "wr_iot_aux_close_retry_release(",
                "wr_iot_aux_close_claim_after_down(")
    if (any(body.count(token) != 1 for token in required) or
            body.count("wr_iot_aux_close_finalize_after_down(") != 3 or
            body.count("wr_iot_virtual_down_checked(") != 2):
        parser.error("WDS checked-close sequence changed")
    fixture = r'''#include "aux-close-claim.h"
#include <assert.h>
#include <stddef.h>
#include <stdio.h>
#define WDEV_NUM_MAX 2
#define NDIS_STATUS_SUCCESS 0
#define CONFIG_RA_HW_NAT_WIFI_NEW_ARCH 1
typedef int INT;
typedef unsigned long ULONG;
typedef void VOID;
typedef void *PNET_DEV;
struct adapter {
 int wr_iot_transition_lock,wr_iot_ticket_wait;
 unsigned int VirtualIfCnt;
 struct wr_iot_radio_transition wr_iot_transition;
 struct wr_iot_interface_ref wr_iot_interface_refs[WDEV_NUM_MAX+1];
};
typedef struct adapter *PRTMP_ADAPTER;
static struct adapter *active_adapter;
static int held,pins,queue_stops,hnat_dereg,wakes,fail_down,down_calls,late_epoch_change;
#define RTMP_OS_NETDEV_GET_PRIV(dev) (active_adapter)
#define RTMP_IRQ_LOCK(lock,flags) do {(void)(lock);(flags)=0;assert(!held);held=1;}while(0)
#define RTMP_IRQ_UNLOCK(lock,flags) do {(void)(lock);(void)(flags);assert(held);held=0;}while(0)
#define VIRTUAL_IF_NUM(ad) ((ad)->VirtualIfCnt)
#define RTMP_OS_NETDEV_STOP_QUEUE(dev) do {(void)(dev);++queue_stops;}while(0)
#define RT_MOD_HNAT_DEREG(dev) do {(void)(dev);++hnat_dereg;}while(0)
#define RT_MOD_DEC_USE_COUNT() (--pins)
#define wake_up_all(p) do {(void)(p);++wakes;}while(0)
static int wr_iot_virtual_down_checked(struct adapter *ad,
 const struct wr_iot_radio_ticket *ticket){
 assert(!held);
 ++down_calls;
 if(fail_down)return 1;
 assert(ticket->operation==WR_RADIO_AUX_CLOSE&&ad->VirtualIfCnt>1);
 assert(ad->wr_iot_transition.busy==ticket->operation);
 --ad->VirtualIfCnt;ad->wr_iot_transition.virtual_down_stage=2;
 if(late_epoch_change)ad->wr_iot_transition.epoch++;
 return NDIS_STATUS_SUCCESS;
}
''' + body + r'''
static void setup(struct adapter *ad,int *main_dev,int *wds_dev,int last){
 unsigned long seq=0;
 struct wr_iot_interface_ref *main_ref,*wds_ref;
 *ad=(struct adapter){0};active_adapter=ad;
 wr_iot_radio_transition_init(&ad->wr_iot_transition);
 ad->wr_iot_transition.phase=WR_RADIO_READY;
 ad->wr_iot_transition.main_ready=1;
 main_ref=wr_iot_registry_add_family(ad->wr_iot_interface_refs,
  WDEV_NUM_MAX+1,&seq,main_dev,WR_REF_FAMILY_MAIN);
 wds_ref=wr_iot_registry_add_family(ad->wr_iot_interface_refs,
  WDEV_NUM_MAX+1,&seq,wds_dev,WR_REF_FAMILY_WDS);
 assert(main_ref&&wds_ref);
 main_ref->published=wds_ref->published=1;
 main_ref->phase=last?WR_REF_IDLE:WR_REF_OWNED;
 main_ref->last_token=1;
 wds_ref->phase=WR_REF_OWNED;wds_ref->last_token=1;
 ad->VirtualIfCnt=last?1:2;
 held=queue_stops=hnat_dereg=wakes=fail_down=down_calls=late_epoch_change=0;pins=1;
}
int main(void){
 struct adapter ad;
 int main_dev=0,wds_dev=0;
 setup(&ad,&main_dev,&wds_dev,0);
 assert(WdsVirtualIF_close(&wds_dev)==0);
 assert(ad.VirtualIfCnt==1&&pins==0&&queue_stops==1&&hnat_dereg==1&&wakes==1);
 assert(ad.wr_iot_interface_refs[1].phase==WR_REF_IDLE&&!ad.wr_iot_transition.busy);
 setup(&ad,&main_dev,&wds_dev,0);fail_down=1;
 assert(WdsVirtualIF_close(&wds_dev)==-1);
 assert(ad.VirtualIfCnt==2&&pins==1&&queue_stops==1&&hnat_dereg==1&&wakes==0);
 assert(ad.wr_iot_interface_refs[1].phase==WR_REF_CLOSING&&
        ad.wr_iot_interface_refs[1].close_stage==1&&
        ad.wr_iot_transition.busy==WR_RADIO_AUX_CLOSE);
 assert(WdsVirtualIF_close_retry(&wds_dev)==-1);
 assert(ad.wr_iot_interface_refs[1].close_stage==1&&pins==1&&
        ad.VirtualIfCnt==2&&queue_stops==1&&hnat_dereg==1);
 fail_down=0;
 assert(WdsVirtualIF_close_retry(&wds_dev)==0);
 assert(ad.VirtualIfCnt==1&&pins==0&&queue_stops==1&&hnat_dereg==1&&
        down_calls==3&&ad.wr_iot_interface_refs[1].phase==WR_REF_IDLE);
 setup(&ad,&main_dev,&wds_dev,0);late_epoch_change=1;
 assert(WdsVirtualIF_close(&wds_dev)==-1);
 assert(ad.VirtualIfCnt==1&&pins==1&&down_calls==1&&
        ad.wr_iot_interface_refs[1].close_stage==4);
 assert(WdsVirtualIF_close_complete(&wds_dev)==-1);
 assert(ad.VirtualIfCnt==1&&pins==1&&down_calls==1&&
        ad.wr_iot_interface_refs[1].close_stage==4);
 ad.wr_iot_transition.reset_pending=WR_RADIO_RESET_PDMA;
 assert(WdsVirtualIF_close_complete(&wds_dev)==0);
 assert(ad.VirtualIfCnt==1&&pins==0&&down_calls==1&&
        ad.wr_iot_interface_refs[1].phase==WR_REF_IDLE);
 setup(&ad,&main_dev,&wds_dev,1);
 assert(WdsVirtualIF_close(&wds_dev)==-1);
 assert(ad.VirtualIfCnt==1&&pins==1&&queue_stops==0&&hnat_dereg==0);
 puts("PASS extracted WDS close, same-ticket retry, post-DOWN completion");
 return 0;
}
'''
    args.output.write_text(fixture, encoding="utf-8")
    print(f"Extracted WDS checked close: {args.output}")


if __name__ == "__main__":
    main()
