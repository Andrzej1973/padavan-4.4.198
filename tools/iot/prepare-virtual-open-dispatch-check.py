#!/usr/bin/env python3
"""Extract the isolated claimed UP branch into a host C fixture."""

import argparse
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("candidate", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output must be a new file")
    driver = args.candidate.resolve()
    source = (driver / "common/cmm_cfg.c").read_text(encoding="utf-8")
    start = source.index("\t\t\tif (pInfConf->owner_generation ||")
    end = source.index("\t\t\t/* Arithmetic guard only;", start)
    branch = source[start:end]
    # The combined candidate retains a separate physical START/MAIN_OPEN
    # branch. This fixture extracts only the shared MBSS/AUX increment below
    # it; the source preparer checks that the main branch remains intact.
    main_start = branch.find("if (claim.operation == WR_RADIO_START ||")
    if main_start >= 0:
        aux_start = branch.index("valid = VIRTUAL_IF_NUM(pAd) > 0 &&", main_start)
        branch = branch[:main_start] + branch[aux_start:]
    required = ("wr_iot_virtual_open_claim_matches",
                "wr_iot_virtual_aux_open_claim_matches", "VIRTUAL_IF_INC(pAd)",
                "virtual_up_stage=1U", "RTMP_IRQ_LOCK", "RTMP_IRQ_UNLOCK")
    if any(branch.count(token) != 1 for token in required):
        parser.error("claimed dispatcher branch changed")
    fixture = r'''#include "virtual-open-claim.h"
#include <assert.h>
#include <stdio.h>
#define IN
#define CONFIG_AP_SUPPORT 1
#define WDEV_NUM_MAX 1
#define NDIS_STATUS_FAILURE 1
typedef unsigned int UINT;
typedef unsigned long ULONG;
typedef void VOID;
struct adapter {
 int wr_iot_transition_lock;
 unsigned int VirtualIfCnt;
 void *net_dev;
 struct wr_iot_radio_transition wr_iot_transition;
 struct wr_iot_interface_ref wr_iot_interface_refs[WDEV_NUM_MAX+1];
};
typedef struct adapter *PRTMP_ADAPTER;
typedef struct request {
 VOID *if_dev;
 unsigned long owner_generation,owner_serial,owner_epoch;
 int owner_operation;
} RT_CMD_INF_UP_DOWN;
static int held,beacons;
#define RTMP_IRQ_LOCK(lock,flags) do { (void)(lock);(flags)=0;assert(!held);held=1; } while(0)
#define RTMP_IRQ_UNLOCK(lock,flags) do { (void)(lock);(void)(flags);assert(held);held=0; } while(0)
#define VIRTUAL_IF_NUM(ad) ((ad)->VirtualIfCnt)
#define VIRTUAL_IF_INC(ad) ((ad)->VirtualIfCnt++)
void APMakeAllBssBeacon(PRTMP_ADAPTER ad){assert(ad&&!held);beacons++;}
void APUpdateAllBeaconFrame(PRTMP_ADAPTER ad){assert(ad&&!held);beacons++;}
static int checked_up(PRTMP_ADAPTER pAd,RT_CMD_INF_UP_DOWN *pInfConf){
 int has_claim=pInfConf->owner_generation||pInfConf->owner_serial||
   pInfConf->owner_epoch||pInfConf->owner_operation;
 if(!has_claim)return 2; /* legacy route is outside this extracted fixture */
 do {
''' + branch + r'''
 }while(0);
 return 0;
}
int main(void){
 struct adapter ad={0};
 struct wr_iot_radio_ticket ticket;
 struct wr_iot_interface_ref *record;
 RT_CMD_INF_UP_DOWN request={0};
 unsigned long sequence=0;
 int device=0,other=0,aux=0;
 wr_iot_radio_transition_init(&ad.wr_iot_transition);
 ad.wr_iot_transition.phase=WR_RADIO_READY;
 ad.wr_iot_transition.main_ready=1;
 ad.VirtualIfCnt=1;
 record=wr_iot_registry_add(ad.wr_iot_interface_refs,WDEV_NUM_MAX+1,
                            &sequence,&device);
 assert(record);record->published=1;
 assert(wr_iot_radio_begin(&ad.wr_iot_transition,
   ad.wr_iot_transition.epoch,WR_RADIO_BSS_OPEN,&ticket));
 assert(wr_iot_ref_reserve(record,&device,record->generation,ticket.serial));
 request.if_dev=&device;request.owner_generation=record->generation;
 request.owner_serial=ticket.serial;request.owner_epoch=ticket.epoch;
 request.owner_operation=ticket.operation;
 assert(checked_up(&ad,&request)==0&&ad.VirtualIfCnt==2&&beacons==2&&!held);
 assert(checked_up(&ad,&request)==NDIS_STATUS_FAILURE&&
        ad.VirtualIfCnt==2&&beacons==2&&!held);
 request.if_dev=&other;
 assert(checked_up(&ad,&request)==NDIS_STATUS_FAILURE&&ad.VirtualIfCnt==2);
 request.if_dev=&device;request.owner_serial=0;
 assert(checked_up(&ad,&request)==NDIS_STATUS_FAILURE&&ad.VirtualIfCnt==2);
 ad.net_dev=&device;
 record=wr_iot_registry_add_family(ad.wr_iot_interface_refs,
   WDEV_NUM_MAX+1,&sequence,&aux,WR_REF_FAMILY_APCLI);
 assert(record);record->published=1;
 ad.wr_iot_transition.busy=0;
 ad.wr_iot_transition.virtual_up_stage=0;
 assert(wr_iot_radio_begin_aux_open(&ad.wr_iot_transition,
   ad.VirtualIfCnt,&ticket));
 assert(wr_iot_ref_reserve(record,&aux,record->generation,ticket.serial));
 request.if_dev=&aux;request.owner_generation=record->generation;
 request.owner_serial=ticket.serial;request.owner_epoch=ticket.epoch;
 request.owner_operation=ticket.operation;
 assert(checked_up(&ad,&request)==0&&ad.VirtualIfCnt==3&&beacons==4&&!held);
 assert(checked_up(&ad,&request)==NDIS_STATUS_FAILURE&&ad.VirtualIfCnt==3);
 puts("PASS extracted virtual UP: MBSS and auxiliary claims, replay rejected");
 return 0;
}
'''
    args.output.write_text(fixture, encoding="utf-8")
    print(f"Extracted claimed virtual-UP branch: {args.output}")


if __name__ == "__main__":
    main()
