#!/usr/bin/env python3
"""Actual aggregate hardware transaction; individual actors and MMIO injected."""
import argparse
from pathlib import Path
import subprocess
import tempfile
p=argparse.ArgumentParser(description=__doc__);p.add_argument('candidate',type=Path);a=p.parse_args()
sdk=(a.candidate/'include/iface/rtmp_reg_pcirbs.h').read_text()
start=sdk.rfind('#ifdef RT_BIG_ENDIAN',0,sdk.index('typedef\tunion _WPDMA_GLO_CFG_STRUC'))
end=sdk.index('#endif /* RT_BIG_ENDIAN */',start)+len('#endif /* RT_BIG_ENDIAN */')
fixture=r'''
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include "mcu-boot-ticket.h"
typedef int INT32;typedef unsigned long ULONG;typedef uint32_t UINT32;
@@LAYOUT@@
#define NDIS_STATUS_SUCCESS 0
#define NDIS_STATUS_FAILURE 1
#define MT_WPDMA_GLO_CFG 1
#define MCU_INIT 0
#define fRTMP_ADAPTER_NIC_NOT_EXIST 1u
#define fRTMP_ADAPTER_RESET_IN_PROGRESS 2u
#define fRTMP_ADAPTER_HALT_IN_PROGRESS 4u
typedef struct {unsigned wr_iot_boot_hw_state,wr_iot_boot_hw_stage,wr_iot_boot_mcu_only,wr_iot_boot_frozen,wr_iot_boot_failed,wr_iot_boot_ring_stage,wr_iot_boot_ring_busy,wr_iot_boot_ring_failed,wr_iot_boot_ctrl_state,wr_iot_boot_rx_state,wr_iot_boot_irq_state,wr_iot_boot_irq_unmask_state,wr_iot_boot_dma_state,wr_iot_boot_dma_saved_valid,wr_iot_boot_dma_saved_off,wr_iot_boot_dma_stop_verified,flags;struct {unsigned flags;} MCUCtrl;int wr_iot_transition_lock,wr_iot_mcu_sender_lock;struct wr_iot_mcu_boot_ticket ticket;unsigned ledger[5];} RTMP_ADAPTER;
static unsigned fault,held,calls,reads,aborts,stops,context;
#define in_atomic() 0
#define irqs_disabled() 0
#define OS_TEST_BIT(bit,p) ((void)(bit),*(p)&1)
#define RTMP_TEST_FLAG(ad,f) ((ad)->flags&(f))
#define RTMP_IRQ_LOCK(l,f) do{(void)(l);(f)=0;assert(!held);held=1;}while(0)
#define RTMP_IRQ_UNLOCK(l,f) do{(void)(l);(void)(f);assert(held==1);held=0;}while(0)
#define RTMP_SPIN_LOCK_IRQSAVE(l,f) do{(void)(l);*(f)=0;assert(held==1);held=2;}while(0)
#define RTMP_SPIN_UNLOCK_IRQRESTORE(l,f) do{(void)(l);(void)(f);assert(held==2);held=1;}while(0)
#define RTMP_IO_READ32(ad,reg,out) do{assert(ad&&(reg)==1&&!held);reads++;*(out)=fault==15?~0u:0x52000855;}while(0)
static int wr_iot_mcu_boot_peer_matches(RTMP_ADAPTER *ad,unsigned long serial){assert(ad&&!held);return context&&serial==ad->ticket.peer_serial;}
static int wr_iot_mcu_boot_context_matches(RTMP_ADAPTER *ad,const struct wr_iot_mcu_boot_ticket *t){assert(held==2);if(fault==19&&ad->wr_iot_boot_hw_stage==2)ad->flags|=1;return context&&!ad->wr_iot_boot_failed&&!memcmp(t,&ad->ticket,sizeof(*t))&&!(fault==17&&ad->wr_iot_boot_hw_stage==6);}
static int wr_iot_mcu_boot_matches(RTMP_ADAPTER *ad,const struct wr_iot_mcu_boot_ticket *t){return !ad->wr_iot_boot_frozen&&wr_iot_mcu_boot_context_matches(ad,t);}
static int wr_iot_mcu_boot_frozen_owned(RTMP_ADAPTER *ad){assert(!held);return context&&ad->wr_iot_boot_frozen&&!ad->wr_iot_boot_failed;}
INT32 wr_iot_mcu_boot_hardware_prepare(RTMP_ADAPTER *,const struct wr_iot_mcu_boot_ticket *);
static int op(RTMP_ADAPTER *ad,unsigned stage){
 assert(!held&&ad->wr_iot_boot_hw_state==1&&ad->wr_iot_boot_hw_stage==stage-1&&++calls==stage);
 if(fault==13){unsigned n=calls;assert(wr_iot_mcu_boot_hardware_prepare(ad,&ad->ticket)==1&&calls==n&&!ad->wr_iot_boot_failed);}
 if(stage==1){ad->wr_iot_boot_frozen=1;ad->MCUCtrl.flags=0;ad->wr_iot_boot_mcu_only=0;}
 if(stage==2)ad->MCUCtrl.flags=1;
 if(stage==3)ad->wr_iot_boot_mcu_only=1;
 if(stage==5){ad->wr_iot_boot_dma_saved_off=0x52000850;ad->wr_iot_boot_dma_saved_valid=1;ad->wr_iot_boot_dma_state=2;}
 if(stage==6)ad->wr_iot_boot_irq_unmask_state=2;
 if(fault>=7&&fault<=12&&stage==fault-6)context=0;
 if(fault==18&&stage==2)ad->ticket.radio_epoch++;
 return fault==stage||(fault==14&&stage==6)?1:0;
}
static int wr_iot_mcu_boot_ring_transaction(RTMP_ADAPTER *ad,const struct wr_iot_mcu_boot_ticket *t){assert(t);return op(ad,1);}
static int wr_iot_mcu_boot_controller_init(RTMP_ADAPTER *ad){return op(ad,2);}
static int wr_iot_mcu_boot_rx_restart(RTMP_ADAPTER *ad){return op(ad,3);}
static int wr_iot_mcu_boot_irq_prepare(RTMP_ADAPTER *ad){return op(ad,4);}
static int wr_iot_mcu_boot_dma_start(RTMP_ADAPTER *ad){return op(ad,5);}
static int wr_iot_mcu_boot_irq_unmask(RTMP_ADAPTER *ad){return op(ad,6);}
/* The aggregate fixture injects its actors.  The full retirement protocol is
 * executed by check-mcu-boot-retired-boundary.py; retain this narrow actor
 * here so existing six-stage failure assertions keep their meaning. */
static int wr_iot_mcu_boot_retired_boundary(RTMP_ADAPTER *ad,const struct wr_iot_mcu_boot_ticket *t)
{ assert(ad&&t&&!held&&ad->wr_iot_boot_hw_stage==1);return 0; }
static int wr_iot_nettask_boot_irq_abort(RTMP_ADAPTER *ad){assert(!held&&ad->wr_iot_boot_failed&&ad->wr_iot_boot_irq_unmask_state==1&&ad->wr_iot_boot_hw_state==1);aborts++;return 0;}
static int wr_iot_mcu_boot_dma_stop_hw(RTMP_ADAPTER *ad){
 assert(!held&&aborts==1&&ad->wr_iot_boot_dma_state==1);stops++;
 if(fault==15){assert(!ad->wr_iot_boot_dma_saved_valid);return 1;}
 assert(ad->wr_iot_boot_dma_saved_valid&&ad->wr_iot_boot_dma_saved_off==(calls>=5?0x52000850u:0x52000810u));
 ad->wr_iot_boot_dma_stop_verified=fault==14?0:1;return fault==14?1:0;
}
'''.replace('@@LAYOUT@@',sdk[start:end])+(a.candidate/'include/wr-iot-mcu-boot-hardware.inc').read_text()+r'''
int main(void){
 for(fault=0;fault<=20;fault++){
  RTMP_ADAPTER ad={0};ad.ticket=(struct wr_iot_mcu_boot_ticket){1,2,3,4,5};
  held=calls=reads=aborts=stops=0;context=1;ad.MCUCtrl.flags=ad.wr_iot_boot_mcu_only=1;
  for(unsigned i=0;i<5;i++)ad.ledger[i]=100+i;
  if(fault==16)ad.wr_iot_boot_ctrl_state=1;
  if(fault==20)ad.flags=1;
  unsigned success=fault==0||fault==13,refused=fault==16||fault==20;
  assert(wr_iot_mcu_boot_hardware_prepare(&ad,&ad.ticket)==(success?0:1)&&!held);
  for(unsigned i=0;i<5;i++)assert(ad.ledger[i]==100+i);
  if(refused){assert(!reads&&!calls&&!aborts&&!stops&&!ad.wr_iot_boot_hw_state&&!ad.wr_iot_boot_failed);continue;}
  unsigned last=fault>=1&&fault<=6?fault-1:fault>=7&&fault<=12?fault-7:fault==14?5:fault==15?0:fault==18?1:fault==19?2:6;
  assert(ad.wr_iot_boot_hw_stage==last&&ad.wr_iot_boot_hw_state==(success?2u:3u));
  assert(aborts==(unsigned)!success&&stops==aborts&&ad.wr_iot_boot_failed==(unsigned)!success);
  if(!success)assert(ad.wr_iot_boot_dma_state==(fault==14||fault==15?4u:3u)&&ad.wr_iot_boot_irq_unmask_state==3);
  unsigned previous=calls;assert(wr_iot_mcu_boot_hardware_prepare(&ad,&ad.ticket)==1&&calls==previous);
 }
 puts("PASS actual six-stage hardware transaction: every actor/boundary failure, initial DMA snapshot/bus error, late identity/NIC and nested/duplicate refusal, IRQ block before verified/unknown DMA stop; ledger unchanged, subactors injected");
}
'''
with tempfile.TemporaryDirectory(prefix='wr-mcu-hardware-') as td:
 c=Path(td)/'check.c';c.write_text(fixture)
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(a.candidate/'include'),str(c),'-o',td+'/check'],check=True)
 subprocess.run([td+'/check'],check=True)
