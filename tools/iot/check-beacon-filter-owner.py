#!/usr/bin/env python3
"""Execute actual generated recovery wrapper with reentrant BSS caller injection."""
import argparse,subprocess,tempfile
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('driver',type=Path);a=p.parse_args()
s=(a.driver/'hw_ctrl/cmm_asic_mt.c').read_text()
sig='VOID APCheckBcnQHandler(RTMP_ADAPTER *pAd, INT apidx, BOOLEAN *is_pretbtt_int)'
assert s.count(sig)==1
start=s.index(sig);body=s[start:s.index('\n}',start)+2]
pre=r'''
#include <assert.h>
#include <stdio.h>
#include "beacon-filter-owner.h"
#define MT7603 1
#define MT_MAC 1
#define RTMP_PCI_SUPPORT 1
#define FALSE 0
typedef void VOID;typedef int INT;typedef int BOOLEAN;
typedef struct {int mt,BcnRingLock;struct wr_iot_beacon_filter_owner wr_iot_beacon_filter_owner;} RTMP_ADAPTER;
static int locked,calls,reenter,early;
#define IS_MT7603(ad) ((ad)->mt)
#define RTMP_SEM_LOCK(p) do{(void)(p);assert(!locked);locked=1;}while(0)
#define RTMP_SEM_UNLOCK(p) do{(void)(p);assert(locked);locked=0;}while(0)
#include "beacon-filter-owner-kernel.h"
VOID APCheckBcnQHandler(RTMP_ADAPTER *,INT,BOOLEAN *);
static VOID wr_iot_APCheckBcnQHandler_inner(RTMP_ADAPTER *ad,INT bss,BOOLEAN *out){
 assert(!locked&&bss>=0);calls++;
 if(reenter){BOOLEAN nested=1;reenter=0;APCheckBcnQHandler(ad,1,&nested);assert(!nested);}
 if(early)return;
 *out=1;
}
'''
post=r'''
int main(void){
 RTMP_ADAPTER ad={.mt=1};BOOLEAN result=1;unsigned long token=0,old;
 APCheckBcnQHandler(NULL,0,&result);assert(!result&&!calls);
 APCheckBcnQHandler(&ad,0,NULL);assert(!calls);
 assert(wr_iot_bcn_filter_enter(&ad,&token));old=token;
 APCheckBcnQHandler(&ad,0,&result);assert(!result&&!calls);
 assert(wr_iot_bcn_filter_leave(&ad,token));
 assert(wr_iot_bcn_filter_enter(&ad,&token)&&token!=old);
 assert(!wr_iot_bcn_filter_leave(&ad,old)&&ad.wr_iot_beacon_filter_owner.busy==token);
 assert(wr_iot_bcn_filter_leave(&ad,token));
 reenter=1;APCheckBcnQHandler(&ad,2,&result);
 assert(result&&calls==1&&!ad.wr_iot_beacon_filter_owner.busy&&!locked);
 early=1;APCheckBcnQHandler(&ad,0,&result);assert(!result&&calls==2&&!ad.wr_iot_beacon_filter_owner.busy);
 ad.wr_iot_beacon_filter_owner.serial=~0UL;result=1;
 APCheckBcnQHandler(&ad,0,&result);assert(!result&&calls==2);
 ad.mt=0;early=0;APCheckBcnQHandler(&ad,0,&result);assert(result&&calls==3);
 puts("PASS actual recovery wrapper: shared BSS exclusion, reentry, early return release, stale token and exhaustion refusal, other chip bypass; vendor body injected, no MMIO proof");
}
'''
with tempfile.TemporaryDirectory(prefix='wr-iot-filter-owner-') as d:
 src=Path(d)/'t.c';exe=Path(d)/'t';src.write_text(pre+body+post)
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(a.driver/'include'),str(src),'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)
