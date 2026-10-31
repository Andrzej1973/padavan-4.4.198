#!/usr/bin/env python3
"""Extract WDS removal and phase guard into injected host retention checks."""
import argparse
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('candidate',type=Path);p.add_argument('output',type=Path)
a=p.parse_args()
if a.output.exists():p.error('output must be new')
s=(a.candidate/'ap/ap_wds.c').read_text(encoding='utf-8')
start='INT WDS_Remove(';end='BOOLEAN WDS_StatsGet('
if s.count(start)!=1 or s.count(end)!=1:p.error('WDS remove boundaries changed')
body=s[s.index(start):s.index(end)]
order=['wr_iot_netdev_mark_removing(', 'RtmpOSNetDevProtect(1)',
       'RtmpOSNetDevClose(', 'wr_iot_netdev_close_phase_idle(',
       'RtmpOSNetDevDetach(', 'rtmp_wdev_idx_unreg(', 'RtmpOSNetDevFree(']
if any(body.count(t)!=1 for t in order):p.error('WDS remove operation count changed')
positions=[body.index(t) for t in order]
if positions!=sorted(positions):p.error('WDS close/check/detach/free order changed')
s=(a.candidate/'include/wr-iot-netdev-registration.inc').read_text(encoding='utf-8')
start='INT wr_iot_netdev_close_phase_idle(';end='/* Use only when the attempted removal'
if s.count(start)!=1 or s.count(end)!=1:p.error('phase guard boundaries changed')
gate=s[s.index(start):s.index(end)]
PREFIX='#include "interface-registry.h"\n#include <assert.h>\n#include <stddef.h>\n#define WDEV_NUM_MAX 2\n#define MAX_WDS_ENTRY 1\n#define NDIS_STATUS_SUCCESS 0\n#define NDIS_STATUS_FAILURE -1\ntypedef int INT; typedef unsigned int UINT; typedef unsigned long ULONG;\nstruct wifi_dev { void *if_dev; };\nstruct adapter { int wr_iot_transition_lock,wr_iot_registration_inflight; struct wr_iot_interface_ref wr_iot_interface_refs[3]; struct { struct { struct wifi_dev wdev; } WdsEntry[1]; } WdsTab; };\ntypedef struct adapter RTMP_ADAPTER; typedef void *PNET_DEV;\nstatic struct adapter *active; static int lock,protect,closed,detached,freed,unreg,fail_close,fail_mark;\n#define RTMP_IRQ_LOCK(l,f) do{(void)(l);(f)=0;assert(!lock);lock=1;}while(0)\n#define RTMP_IRQ_UNLOCK(l,f) do{(void)(l);(void)(f);assert(lock);lock=0;}while(0)\nstatic int wr_iot_netdev_mark_removing(RTMP_ADAPTER *a,void *d){(void)d;if(fail_mark)return -1;a->wr_iot_interface_refs[0].removing=1;return 0;}\nstatic void RtmpOSNetDevProtect(int v){assert(!lock);if(v){assert(!protect);protect=1;}else {assert(protect);protect=0;}}\nstatic void RtmpOSNetDevClose(void *d){(void)d;assert(protect);closed++;if(!fail_close)active->wr_iot_interface_refs[0].phase=WR_REF_IDLE;}\nstatic void RtmpOSNetDevDetach(void *d){(void)d;assert(protect&&closed&&active->wr_iot_interface_refs[0].phase==WR_REF_IDLE);detached++;}\nstatic void rtmp_wdev_idx_unreg(RTMP_ADAPTER *a,struct wifi_dev *w){(void)a;(void)w;assert(detached&&!protect);unreg++;}\nstatic void RtmpOSNetDevFree(void *d){(void)d;assert(unreg);freed++;}\n'
SUFFIX='static void reset(struct adapter *a,void *dev){*a=(struct adapter){0};active=a;a->WdsTab.WdsEntry[0].wdev.if_dev=dev;a->wr_iot_interface_refs[0].device=dev;a->wr_iot_interface_refs[0].published=1;a->wr_iot_interface_refs[0].phase=WR_REF_OWNED;lock=protect=closed=detached=freed=unreg=fail_close=fail_mark=0;}\nint main(void){struct adapter a;int dev;\nreset(&a,&dev);fail_close=1;assert(WDS_Remove(&a)==-1);assert(closed==1&&!detached&&!freed&&!protect&&a.WdsTab.WdsEntry[0].wdev.if_dev==&dev);\nreset(&a,&dev);fail_mark=1;assert(WDS_Remove(&a)==-1);assert(!closed&&!detached&&!freed&&!protect);\nreset(&a,&dev);a.wr_iot_registration_inflight=1;assert(WDS_Remove(&a)==-1);assert(!detached&&!freed&&!protect);\nreset(&a,&dev);assert(WDS_Remove(&a)==0);assert(closed==1&&detached==1&&freed==1&&!protect&&!a.WdsTab.WdsEntry[0].wdev.if_dev);\n/* Known unresolved retirement: witness only, not accepted lifecycle. */\nassert(a.wr_iot_interface_refs[0].device==&dev && a.wr_iot_interface_refs[0].published);\nreturn 0;}\n'
a.output.write_text(PREFIX+gate+body+SUFFIX,encoding='utf-8')
print('Extracted WDS remove retention fixture; kernel primitives injected')
