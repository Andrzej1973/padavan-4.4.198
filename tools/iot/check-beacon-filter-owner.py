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
#include "radio-transition-api.h"
#define MT7603 1
#define MT_MAC 1
#define RTMP_PCI_SUPPORT 1
#define FALSE 0
typedef unsigned long ULONG;typedef void VOID;typedef int INT;typedef int BOOLEAN;
typedef struct {int mt,BcnRingLock,wr_iot_transition_lock,wr_iot_ticket_wait,wr_iot_tx_drain_wait;struct wr_iot_radio_transition wr_iot_transition;struct wr_iot_beacon_filter_owner wr_iot_beacon_filter_owner;} RTMP_ADAPTER;
static int locked,calls,reenter,early,drain_wakes,reset_inside;
#define IS_MT7603(ad) ((ad)->mt)
#define RTMP_SEM_LOCK(p) do{(void)(p);assert(!locked);locked=1;}while(0)
#define RTMP_SEM_UNLOCK(p) do{(void)(p);assert(locked);locked=0;}while(0)
#define RTMP_IRQ_LOCK(p,f) do{(void)(p);(f)=0;assert(!locked);locked=1;}while(0)
#define RTMP_IRQ_UNLOCK(p,f) do{(void)(p);(void)(f);assert(locked);locked=0;}while(0)
#define wake_up_all(p) do{assert(!locked);(*(p))++;}while(0)
#include "beacon-filter-owner-kernel.h"
VOID APCheckBcnQHandler(RTMP_ADAPTER *,INT,BOOLEAN *);
static VOID wr_iot_APCheckBcnQHandler_inner(RTMP_ADAPTER *ad,INT bss,BOOLEAN *out){
 assert(!locked&&bss>=0);calls++;
 if(reset_inside){
  struct wr_iot_radio_ticket t;
  assert(wr_iot_radio_request_reset_kind(&ad->wr_iot_transition,WR_RADIO_RESET_PDMA));
  assert(!wr_iot_radio_begin(&ad->wr_iot_transition,ad->wr_iot_transition.epoch,WR_RADIO_RESET,&t));
  assert(ad->wr_iot_transition.active_tx==1);
 }
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
 wr_iot_radio_transition_init(&ad.wr_iot_transition);
 ad.wr_iot_transition.phase=WR_RADIO_READY;ad.wr_iot_transition.main_ready=1;
 assert(wr_iot_bcn_filter_enter(&ad,&token));old=token;
 struct wr_iot_radio_ticket reset;
 assert(!wr_iot_radio_begin(&ad.wr_iot_transition,ad.wr_iot_transition.epoch,WR_RADIO_BSS_OPEN,&reset));
 APCheckBcnQHandler(&ad,0,&result);assert(!result&&!calls);
 assert(ad.wr_iot_transition.active_tx==1); /* contention releases only its own lease */
 assert(!ad.wr_iot_tx_drain_wait&&!ad.wr_iot_ticket_wait);
 assert(wr_iot_bcn_filter_leave(&ad,token));
 assert(wr_iot_bcn_filter_enter(&ad,&token)&&token!=old);
 drain_wakes=ad.wr_iot_tx_drain_wait;
 assert(!wr_iot_bcn_filter_leave(&ad,old)&&ad.wr_iot_beacon_filter_owner.busy==token);
 assert(ad.wr_iot_transition.active_tx==1);
 assert(ad.wr_iot_tx_drain_wait==drain_wakes&&ad.wr_iot_ticket_wait==drain_wakes);
 assert(wr_iot_bcn_filter_leave(&ad,token));
 reenter=1;APCheckBcnQHandler(&ad,2,&result);
 assert(result&&calls==1&&!ad.wr_iot_beacon_filter_owner.busy&&!locked);
 early=1;APCheckBcnQHandler(&ad,0,&result);assert(!result&&calls==2&&!ad.wr_iot_beacon_filter_owner.busy);
 ad.wr_iot_beacon_filter_owner.serial=~0UL;result=1;
 APCheckBcnQHandler(&ad,0,&result);assert(!result&&calls==2);
 assert(!ad.wr_iot_transition.active_tx);
 assert(ad.wr_iot_tx_drain_wait>0);
 drain_wakes=ad.wr_iot_tx_drain_wait;
 ad.wr_iot_transition.pm_suspending=1;result=1;
 APCheckBcnQHandler(&ad,0,&result);assert(!result&&calls==2);
 assert(ad.wr_iot_tx_drain_wait==drain_wakes);
 ad.wr_iot_transition.pm_suspending=0;
 ad.wr_iot_beacon_filter_owner.serial=0;
 assert(wr_iot_bcn_filter_enter(&ad,&token));
 assert(wr_iot_radio_request_reset_kind(&ad.wr_iot_transition,WR_RADIO_RESET_PDMA));
 unsigned long epoch=ad.wr_iot_transition.epoch;
 assert(!wr_iot_radio_begin(&ad.wr_iot_transition,epoch,WR_RADIO_RESET,&reset));
 assert(wr_iot_bcn_filter_leave(&ad,token));
 assert(!ad.wr_iot_transition.active_tx&&ad.wr_iot_transition.reset_pending==WR_RADIO_RESET_PDMA);
 assert(!wr_iot_bcn_filter_enter(&ad,&token));
 assert(wr_iot_radio_begin(&ad.wr_iot_transition,epoch,WR_RADIO_RESET,&reset));
 assert(wr_iot_radio_finish(&ad.wr_iot_transition,&reset,0));
 /* Inject reset intent from the actual wrapped vendor-body call. */
 wr_iot_radio_transition_init(&ad.wr_iot_transition);
 ad.wr_iot_transition.phase=WR_RADIO_READY;ad.wr_iot_transition.main_ready=1;
 reset_inside=1;early=0;APCheckBcnQHandler(&ad,2,&result);reset_inside=0;
 assert(result&&calls==3&&!ad.wr_iot_transition.active_tx);
 assert(ad.wr_iot_transition.reset_pending==WR_RADIO_RESET_PDMA);
 assert(wr_iot_radio_begin(&ad.wr_iot_transition,ad.wr_iot_transition.epoch,WR_RADIO_RESET,&reset));
 assert(wr_iot_radio_finish(&ad.wr_iot_transition,&reset,0));
 /* Real suspend admission must fence new recovery while the old lease drains. */
 wr_iot_radio_transition_init(&ad.wr_iot_transition);
 ad.wr_iot_transition.phase=WR_RADIO_READY;ad.wr_iot_transition.main_ready=1;
 assert(wr_iot_bcn_filter_enter(&ad,&token));
 assert(wr_iot_radio_request_suspend(&ad.wr_iot_transition));
 assert(ad.wr_iot_transition.active_tx==1);
 unsigned long refused=123;
 assert(!wr_iot_bcn_filter_enter(&ad,&refused)&&refused==0);
 drain_wakes=ad.wr_iot_tx_drain_wait;
 assert(wr_iot_bcn_filter_leave(&ad,token));
 assert(!ad.wr_iot_transition.active_tx&&ad.wr_iot_transition.pm_suspending);
 assert(ad.wr_iot_tx_drain_wait==drain_wakes+1);
 assert(ad.wr_iot_ticket_wait==ad.wr_iot_tx_drain_wait);
 ad.mt=0;early=0;APCheckBcnQHandler(&ad,0,&result);assert(result&&calls==4);
 puts("PASS actual recovery wrapper: shared BSS exclusion, reentry, early return release, stale token and exhaustion refusal, other chip bypass; vendor body injected, no MMIO proof");
}
'''
with tempfile.TemporaryDirectory(prefix='wr-iot-filter-owner-') as d:
 src=Path(d)/'t.c';exe=Path(d)/'t';src.write_text(pre+body+post)
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(a.driver/'include'),str(src),'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)
