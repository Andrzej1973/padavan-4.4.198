#!/usr/bin/env python3
"""Actual four-stage transaction with injected suboperations and ownership loss."""
import argparse
from pathlib import Path
import subprocess
import tempfile
p=argparse.ArgumentParser(description=__doc__);p.add_argument('candidate',type=Path);a=p.parse_args()
fixture=r'''
#include <assert.h>
#include <stdio.h>
#include <string.h>
typedef int INT32;typedef unsigned long ULONG;
#define NDIS_STATUS_FAILURE 1
#define NDIS_STATUS_SUCCESS 0
struct wr_iot_mcu_boot_ticket {unsigned long peer_serial,radio_serial,radio_epoch,close_serial,close_epoch;};
typedef struct {unsigned wr_iot_boot_ring_stage,wr_iot_boot_ring_busy,wr_iot_boot_ring_failed,wr_iot_boot_failed,wr_iot_boot_frozen;int wr_iot_transition_lock,wr_iot_mcu_sender_lock;struct wr_iot_mcu_boot_ticket ticket;} RTMP_ADAPTER;
static unsigned held,calls,fault,peer,context,final_context_reads,atomic_context,irq_off;
#define in_atomic() atomic_context
#define irqs_disabled() irq_off
#define RTMP_IRQ_LOCK(l,f) do{(void)(l);(f)=0;assert(!held);held=1;}while(0)
#define RTMP_IRQ_UNLOCK(l,f) do{(void)(l);(void)(f);assert(held==1);held=0;}while(0)
#define RTMP_SPIN_LOCK_IRQSAVE(l,f) do{(void)(l);*(f)=0;assert(held==1);held=2;}while(0)
#define RTMP_SPIN_UNLOCK_IRQRESTORE(l,f) do{(void)(l);(void)(f);assert(held==2);held=1;}while(0)
static int wr_iot_mcu_boot_peer_matches(RTMP_ADAPTER *ad,unsigned long serial){assert(ad&&!held);return peer&&serial==ad->ticket.peer_serial;}
static int wr_iot_mcu_boot_context_matches(RTMP_ADAPTER *ad,const struct wr_iot_mcu_boot_ticket *t){
 assert(held==2);if(fault==14&&ad->wr_iot_boot_ring_stage==4&&++final_context_reads==1)return 0;
 return context&&!ad->wr_iot_boot_failed&&!memcmp(t,&ad->ticket,sizeof(*t));
}
static int wr_iot_mcu_boot_matches(RTMP_ADAPTER *ad,const struct wr_iot_mcu_boot_ticket *t){return !ad->wr_iot_boot_frozen&&wr_iot_mcu_boot_context_matches(ad,t);}
static int wr_iot_mcu_boot_frozen_owned(RTMP_ADAPTER *ad){assert(!held);return context&&ad->wr_iot_boot_frozen&&!ad->wr_iot_boot_failed;}
INT32 wr_iot_mcu_boot_ring_transaction(RTMP_ADAPTER *,const struct wr_iot_mcu_boot_ticket *);
static int operation(RTMP_ADAPTER *ad,unsigned stage){
 assert(ad&&!held&&ad->wr_iot_boot_ring_busy&&ad->wr_iot_boot_ring_stage==stage-1);
 assert(++calls==stage);if(stage==1)ad->wr_iot_boot_frozen=1;
 if(fault==13){unsigned saved=calls;assert(wr_iot_mcu_boot_ring_transaction(ad,&ad->ticket)==1);assert(calls==saved&&!ad->wr_iot_boot_failed);}
 if(fault>=5&&fault<=8&&stage==fault-4)context=0;
 if(fault>=9&&fault<=12&&stage==fault-8)peer=0;
 if(fault==15&&stage==2)ad->ticket.radio_epoch++;
 return fault==stage?1:0;
}
static int wr_iot_mcu_boot_rom_quiesce(RTMP_ADAPTER *ad){return operation(ad,1);}
static int wr_iot_mcu_boot_rx_refresh(RTMP_ADAPTER *ad){return operation(ad,2);}
static int wr_iot_mcu_boot_control_retire(RTMP_ADAPTER *ad){return operation(ad,3);}
static int wr_iot_mcu_boot_ring_rearm(RTMP_ADAPTER *ad){return operation(ad,4);}
'''+(a.candidate/'include/wr-iot-mcu-boot-ring-transaction.inc').read_text()+r'''
int main(void){
 for(fault=0;fault<=15;fault++){
  RTMP_ADAPTER ad={0};ad.ticket=(struct wr_iot_mcu_boot_ticket){1,2,3,4,5};
  held=calls=final_context_reads=atomic_context=irq_off=0;peer=context=1;
  int ret=wr_iot_mcu_boot_ring_transaction(&ad,&ad.ticket);
  int success=fault==0||fault==13;assert(ret==(success?0:1)&&!held&&!ad.wr_iot_boot_ring_busy);
  unsigned expected=fault>=1&&fault<=4?fault-1:fault>=5&&fault<=8?fault-5:fault>=9&&fault<=12?fault-9:fault==15?1:4;
  assert(ad.wr_iot_boot_ring_stage==expected&&ad.wr_iot_boot_ring_failed==(unsigned)!success&&ad.wr_iot_boot_failed==(unsigned)!success);
  unsigned prior=calls;assert(wr_iot_mcu_boot_ring_transaction(&ad,&ad.ticket)==1&&calls==prior);
 }
 fault=0;
 for(unsigned i=0;i<6;i++){
  RTMP_ADAPTER ad={0};ad.ticket=(struct wr_iot_mcu_boot_ticket){1,2,3,4,5};
  struct wr_iot_mcu_boot_ticket supplied=ad.ticket;
  calls=held=atomic_context=irq_off=0;peer=context=1;
  switch(i){case 0:supplied.radio_epoch++;break;case 1:ad.wr_iot_boot_ring_busy=1;break;case 2:ad.wr_iot_boot_ring_failed=1;break;case 3:ad.wr_iot_boot_ring_stage=2;break;case 4:atomic_context=1;break;case 5:irq_off=1;break;}
  assert(wr_iot_mcu_boot_ring_transaction(&ad,&supplied)==1&&!calls&&!ad.wr_iot_boot_failed&&!held);
 }
 puts("PASS actual ring transaction: four-stage order, retained last stage, failures/context/peer drift at each boundary, final context loss, nested/duplicate/wrong-ticket refusal; suboperations injected, no epoch commit");
}
'''
with tempfile.TemporaryDirectory(prefix='wr-mcu-ring-transaction-') as td:
 c=Path(td)/'check.c';c.write_text(fixture)
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-pie','-no-pie',str(c),'-o',td+'/check'],check=True)
 subprocess.run([td+'/check'],check=True)
