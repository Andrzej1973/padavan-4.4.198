#!/usr/bin/env python3
"""Isolated secondary beacon decision guard; no production installation."""
import argparse
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('input', type=Path)
p.add_argument('candidate', type=Path)
p.add_argument('fixture', type=Path)
a = p.parse_args()
if len({x.resolve() for x in (a.input, a.candidate, a.fixture)}) != 3:
    raise SystemExit('Input and outputs must be distinct')
if a.candidate.exists() or a.fixture.exists():
    raise SystemExit('Refusing to overwrite outputs')
source = a.input.read_text(encoding='utf-8')
anchor = 'BOOLEAN BeaconTransmitRequired(RTMP_ADAPTER *pAd, INT apidx, BSS_STRUCT *pMbss)'
if source.count(anchor) != 1:
    raise SystemExit('Beacon decision signature changed')
start = source.index(anchor)
end = source.index('\n}', start) + 2
original = source[start:end]
old = '\t\tif (apidx == MAIN_MBSSID)'
if original.count(old) != 1:
    raise SystemExit('Secondary beacon decision anchor changed')
patched = original.replace(old, '''        /* Stale beacon intent must not authorize a closed secondary BSS.
         * Main BSS/WDS exceptions retain their existing behavior. This does
         * not drain hardware queues or establish RF quiescence. */
        if (apidx != MAIN_MBSSID &&
            (!pMbss->wdev.if_dev ||
             !RTMP_OS_NETDEV_STATE_RUNNING(pMbss->wdev.if_dev)))
            break;

''' + old)
prefix = r'''#include <assert.h>
#include <stdio.h>
typedef int BOOLEAN;
typedef int INT;
typedef unsigned char UCHAR;
struct device {int running;};
struct wdev {struct device *if_dev;};
typedef struct {unsigned int BcnBufIdx;int bBcnSntReq;} BCN_BUF_STRUC;
typedef struct {struct wdev wdev;BCN_BUF_STRUC bcn_buf;} BSS_STRUCT;
typedef struct {struct {int Mode;struct {struct wdev wdev;} WdsEntry[2];} WdsTab;struct {int BssidNum;} ApCfg;} RTMP_ADAPTER;
#define FALSE 0
#define TRUE 1
#define MAIN_MBSSID 0
#define HW_BEACON_MAX_NUM 16
#define MAX_WDS_ENTRY 2
#define WDS_BRIDGE_MODE 1
#define RTMP_OS_NETDEV_STATE_RUNNING(dev) ((dev)->running)
'''
tail = r'''
int main(void){
 RTMP_ADAPTER ad={0};BSS_STRUCT bss={0};struct device dev={0};
 ad.ApCfg.BssidNum=3;bss.bcn_buf.BcnBufIdx=2;bss.bcn_buf.bBcnSntReq=TRUE;
 assert(!BeaconTransmitRequired(&ad,2,&bss));
 bss.wdev.if_dev=&dev;assert(!BeaconTransmitRequired(&ad,2,&bss));
 dev.running=1;assert(BeaconTransmitRequired(&ad,2,&bss));
 bss.bcn_buf.bBcnSntReq=FALSE;assert(!BeaconTransmitRequired(&ad,2,&bss));
 bss.bcn_buf.bBcnSntReq=TRUE;bss.bcn_buf.BcnBufIdx=HW_BEACON_MAX_NUM;
 assert(!BeaconTransmitRequired(&ad,2,&bss));bss.bcn_buf.BcnBufIdx=2;
 dev.running=0;assert(!BeaconTransmitRequired(&ad,1,&bss));
 /* Main decision still follows its original flag and WDS exception. */
 assert(BeaconTransmitRequired(&ad,0,&bss));bss.bcn_buf.bBcnSntReq=FALSE;
 assert(!BeaconTransmitRequired(&ad,0,&bss));
#ifdef WDS_SUPPORT
 ad.WdsTab.WdsEntry[0].wdev.if_dev=&dev;dev.running=1;
 assert(BeaconTransmitRequired(&ad,0,&bss));
 assert(!BeaconTransmitRequired(&ad,2,&bss));
 ad.WdsTab.Mode=WDS_BRIDGE_MODE;bss.bcn_buf.bBcnSntReq=TRUE;
 assert(!BeaconTransmitRequired(&ad,0,&bss)&&!BeaconTransmitRequired(&ad,2,&bss));
#endif
 puts("PASS candidate actual beacon decision: closed/absent secondary rejected, active flag and main/WDS behavior retained; no RF proof");
 return 0;
}
'''
# Vendor pAd is unused when all optional decision features are disabled.
fixture_function = patched.replace('RTMP_ADAPTER *pAd,', 'RTMP_ADAPTER *pAd __attribute__((unused)),', 1)
a.candidate.write_text(source[:start] + patched + source[end:], encoding='utf-8')
a.fixture.write_text(prefix + fixture_function + tail, encoding='utf-8')
print('Prepared isolated beacon decision candidate; production and RF queues unchanged')
