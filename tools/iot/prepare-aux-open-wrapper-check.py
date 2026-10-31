#!/usr/bin/env python3
"""Extract actual isolated auxiliary ndo_open bodies into a host C fixture."""

import argparse
from pathlib import Path


FUNCTIONS = (
    ("ap/ap_wds_inf.c", "INT WdsVirtualIF_open(", "INT WdsVirtualIF_close("),
    ("ap/ap_apcli_inf.c", "INT ApCli_VirtualIF_Open(",
     "INT ApCli_VirtualIF_Close("),
    ("os/linux/rt_profile.c", "INT Monitor_VirtualIF_Open(",
     "INT Monitor_VirtualIF_Close("),
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("driver", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--wds-only", action="store_true")
    args = parser.parse_args()
    driver = args.driver.resolve()
    if args.output.exists():
        parser.error("output must be a new file")
    bodies = []
    for rel, start, end in (FUNCTIONS[:1] if args.wds_only else FUNCTIONS):
        data = (driver / rel).read_text(encoding="utf-8")
        if data.count(start) != 1 or data.count(end) != 1:
            parser.error(f"ambiguous wrapper: {rel}")
        begin = data.index(start)
        body = data[begin:data.index('\n}', begin)+2]
        if (body.count("VIRTUAL_IF_UP_CLAIM(") != 1 or
                body.count("wr_iot_aux_open_accepted(") != 1 or
                "RT_MOD_DEC_USE_COUNT();" in body[body.index("VIRTUAL_IF_UP_CLAIM("):]):
            parser.error(f"unexpected claimed wrapper: {rel}")
        bodies.append(body)
    fixture = r'''#include "virtual-open-claim.h"
#include <assert.h>
#include <stddef.h>
#include <stdio.h>
#define WDEV_NUM_MAX 3
#define NDIS_STATUS_SUCCESS 0
#define CMD_RTPRIV_IOCTL_APC_OPEN 11
#define CMD_RTPRIV_IOCTL_SNIFF_OPEN 12
#define CONFIG_RA_HW_NAT_WIFI_NEW_ARCH 1
#define MTFWD 1
typedef int INT;
typedef unsigned long ULONG;
typedef void *PNET_DEV;
struct adapter {
 int wr_iot_transition_lock,wr_iot_ticket_wait;
 unsigned int VirtualIfCnt;
 void *net_dev;
 struct wr_iot_radio_transition wr_iot_transition;
 struct wr_iot_interface_ref wr_iot_interface_refs[WDEV_NUM_MAX+1];
};
typedef struct adapter *PRTMP_ADAPTER;
static struct adapter *active_adapter;
static int lock_held,pins,hnat,queue,carrier,wakes,fail_up,fail_family,late_reset,family_calls;
#define RT_MOD_INC_USE_COUNT() (++pins)
#define RT_MOD_DEC_USE_COUNT() (--pins)
#define RTMP_OS_NETDEV_GET_PRIV(dev) (active_adapter)
#define RTMP_IRQ_LOCK(lock,flags) do {(void)(lock);(flags)=0;assert(!lock_held);lock_held=1;}while(0)
#define RTMP_IRQ_UNLOCK(lock,flags) do {(void)(lock);(void)(flags);assert(lock_held);lock_held=0;}while(0)
#define VIRTUAL_IF_NUM(ad) ((ad)->VirtualIfCnt)
#define RT_MOD_HNAT_REG(dev) do {(void)(dev);++hnat;}while(0)
#define RTMP_OS_NETDEV_START_QUEUE(dev) do {(void)(dev);++queue;}while(0)
#define RTMP_OS_NETDEV_CARRIER_OFF(dev) do {(void)(dev);++carrier;}while(0)
#define wake_up_all(p) do {(void)(p);++wakes;}while(0)
static int mock_up(struct adapter *ad,void *device,
                   const struct wr_iot_radio_ticket *ticket,unsigned long generation){
 struct wr_iot_virtual_open_claim claim={device,generation,ticket->serial,
                                          ticket->epoch,ticket->operation};
 int valid;
 assert(!lock_held);
 lock_held=1;
 valid=wr_iot_virtual_aux_open_claim_matches(&claim,&ad->wr_iot_transition,
   ad->wr_iot_interface_refs,WDEV_NUM_MAX+1,ad->net_dev,ad->VirtualIfCnt);
 if(valid&&!fail_up){++ad->VirtualIfCnt;ad->wr_iot_transition.virtual_up_stage=1;}
 lock_held=0;
 if(valid&&!fail_up&&late_reset)wr_iot_radio_request_reset(&ad->wr_iot_transition);
 return valid&&!fail_up?0:-1;
}
#define VIRTUAL_IF_UP_CLAIM(ad,dev,ticket,generation) mock_up(ad,dev,ticket,generation)
static int mock_family(int command,void *device){
 (void)device;
 assert(!lock_held);family_calls++;
 assert(command==CMD_RTPRIV_IOCTL_APC_OPEN||command==CMD_RTPRIV_IOCTL_SNIFF_OPEN);
 return fail_family?1:NDIS_STATUS_SUCCESS;
}
#define RTMP_AP_IoctlHandle(ad,p,cmd,a,dev,b) mock_family(cmd,dev)
#define RTMP_COM_IoctlHandle(ad,p,cmd,a,dev,b) mock_family(cmd,dev)
''' + "\n".join(bodies) + r'''
static void reset_case(struct adapter *ad,enum wr_iot_ref_family family,
                       void *main_dev,void *aux_dev){
 unsigned long sequence=0;
 struct wr_iot_interface_ref *record;
 *ad=(struct adapter){0};active_adapter=ad;
 wr_iot_radio_transition_init(&ad->wr_iot_transition);
 ad->wr_iot_transition.phase=WR_RADIO_READY;
 ad->wr_iot_transition.main_ready=1;
 ad->net_dev=main_dev;ad->VirtualIfCnt=1;
 record=wr_iot_registry_add_family(ad->wr_iot_interface_refs,
   WDEV_NUM_MAX+1,&sequence,aux_dev,family);
 assert(record);record->published=1;
 lock_held=pins=hnat=queue=carrier=wakes=fail_up=fail_family=late_reset=family_calls=0;
}
static void check_family(enum wr_iot_ref_family family,
                         INT (*open_fn)(PNET_DEV)){
 struct adapter ad;
 int main_dev=0,aux_dev=0;
 reset_case(&ad,family,&main_dev,&aux_dev);
 assert(open_fn(&aux_dev)==0);
 assert(ad.VirtualIfCnt==2&&pins==1&&hnat==1&&!lock_held);
 assert(ad.wr_iot_interface_refs[0].phase==WR_REF_OWNED);
 assert(family_calls==(family==WR_REF_FAMILY_WDS?0:1));
 reset_case(&ad,family,&main_dev,&aux_dev);
 fail_up=1;
 assert(open_fn(&aux_dev)==-1);
 assert(ad.VirtualIfCnt==1&&pins==1&&hnat==0&&!lock_held);
 assert(ad.wr_iot_interface_refs[0].phase==WR_REF_UNCERTAIN_OPEN);
 assert(!family_calls);
 reset_case(&ad,family,&main_dev,&aux_dev);
 late_reset=1;
 assert(open_fn(&aux_dev)==-1);
 assert(ad.VirtualIfCnt==2&&pins==1&&hnat==0&&!lock_held);
 assert(ad.wr_iot_interface_refs[0].phase==WR_REF_UNCERTAIN_OPEN);
 if(family==WR_REF_FAMILY_WDS)return;
 assert(!family_calls); /* Invalidated between UP and family OPEN. */
 reset_case(&ad,family,&main_dev,&aux_dev);
 fail_family=1;
 assert(open_fn(&aux_dev)==-1);
 assert(ad.VirtualIfCnt==2&&pins==1&&hnat==0&&!lock_held);
 assert(ad.wr_iot_interface_refs[0].phase==WR_REF_UNCERTAIN_OPEN);
 assert(family_calls==1);
}
int main(void){
 check_family(WR_REF_FAMILY_WDS,WdsVirtualIF_open);
 check_family(WR_REF_FAMILY_APCLI,ApCli_VirtualIF_Open);
 check_family(WR_REF_FAMILY_MONITOR,Monitor_VirtualIF_Open);
 puts("PASS extracted WDS/AP-client/monitor open success, failure and late reset");
 return 0;
}
'''
    if args.wds_only:
        fixture=fixture.replace(' check_family(WR_REF_FAMILY_APCLI,ApCli_VirtualIF_Open);','')
        fixture=fixture.replace(' check_family(WR_REF_FAMILY_MONITOR,Monitor_VirtualIF_Open);','')
        first=fixture.index('static int mock_family(')
        last=fixture.index('#define RTMP_AP_IoctlHandle',first)
        fixture=fixture[:first]+fixture[last:]
        fixture=fixture.replace('PASS extracted WDS/AP-client/monitor open success, failure and late reset',
                                'PASS extracted WDS open only, success/failure and late reset')
    if 'wr_iot_wds_configured_interface_open(' in bodies[0]:
        mock=r'''
static int fail_configured,configured_calls;
static int wr_iot_wds_configured_interface_open(struct adapter *ad,void *device,unsigned long generation){
 struct wr_iot_interface_ref *r=wr_iot_registry_find(ad->wr_iot_interface_refs,WDEV_NUM_MAX+1,device,generation);
 assert(!lock_held&&r&&r->phase==WR_REF_OWNED&&r->family==WR_REF_FAMILY_WDS);
 assert(pins==1&&hnat==0&&queue==0);configured_calls++;
 return !fail_configured;
}
'''
        fixture=fixture.replace('INT WdsVirtualIF_open(',mock+'\nINT WdsVirtualIF_open(',1)
        fixture=fixture.replace('lock_held=pins=hnat=queue=carrier=wakes=fail_up=fail_family=late_reset=family_calls=0;',
                                'fail_configured=configured_calls=0;\n lock_held=pins=hnat=queue=carrier=wakes=fail_up=fail_family=late_reset=family_calls=0;',1)
        fixture=fixture.replace('if(family==WR_REF_FAMILY_WDS)return;',r'''
 if(family==WR_REF_FAMILY_WDS){
  reset_case(&ad,family,&main_dev,&aux_dev);fail_configured=1;
  assert(open_fn(&aux_dev)==-1&&configured_calls==1);
  assert(ad.VirtualIfCnt==2&&pins==1&&!hnat&&!queue&&!lock_held);
  assert(ad.wr_iot_interface_refs[0].phase==WR_REF_OWNED);
  reset_case(&ad,family,&main_dev,&aux_dev);ad.VirtualIfCnt=0;
  assert(open_fn(&aux_dev)==-1&&!configured_calls&&!pins&&!hnat&&!queue);
  return;
 }
''',1)
    args.output.write_text(fixture, encoding="utf-8")
    print(f"Extracted {len(bodies)} auxiliary open wrapper(s): {args.output}")


if __name__ == "__main__":
    main()
