#!/usr/bin/env python3
"""Compose final MBSS_Init with actual registry bridge, synthetic OS primitives."""
import argparse
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('driver',type=Path);p.add_argument('fixture',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
if a.output.exists():raise SystemExit('New output required')
s=(a.driver/'ap/ap_mbss.c').read_text();sig='VOID MBSS_Init('
if s.count(sig)!=1:raise SystemExit('Changed final MBSS init')
start=s.index(sig);function=s[start:s.index('\n}',start)+2]
t=a.fixture.read_text()
if t.count(sig)!=1:raise SystemExit('Changed init fixture')
start=t.index(sig);end=t.index('\n}',start)+2
t=t[:start]+'#include "wr-iot-netdev-registration.inc"\n'+function+t[end:]
old='typedef struct {int FlgMbssInit'
if t.count(old)!=1:raise SystemExit('Changed fixture adapter')
t=t.replace(old,'typedef struct {int wr_iot_transition_lock;struct wr_iot_radio_transition wr_iot_transition;struct wr_iot_interface_ref wr_iot_interface_refs[5];unsigned long wr_iot_registration_generation;int FlgMbssInit',1)
prefix='''#include "radio-transition.h"
#include "interface-registry.h"
typedef unsigned long ULONG;
typedef unsigned char UCHAR;
typedef int INT;
#define WDEV_NUM_MAX 4
#define NDIS_STATUS_FAILURE 1
static int wr_test_held;
#define RTMP_IRQ_LOCK(lock,flags) ((flags)=0,assert(!wr_test_held),wr_test_held=1,(void)(lock))
#define RTMP_IRQ_UNLOCK(lock,flags) ((void)(flags),(void)(lock),assert(wr_test_held),wr_test_held=0)
'''
t=prefix+t
t=t.replace('memset(&ad,0,sizeof(ad));','memset(&ad,0,sizeof(ad));wr_iot_radio_transition_init(&ad.wr_iot_transition);')
t=t.replace('MBSS_Init(&ad,&hook);','MBSS_Init(&ad,&hook);{int count=0;for(int n=0;n<5;n++)if(ad.wr_iot_interface_refs[n].device)count++;assert(count==beacons&&!wr_test_held);}')
a.output.write_text(t)
print('Extracted final MBSS construction plus registry bridge; OS operations injected')
