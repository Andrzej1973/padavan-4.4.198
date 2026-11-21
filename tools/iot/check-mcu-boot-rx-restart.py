#!/usr/bin/env python3
"""Actual frozen RX restart coordinator; tasklet actor and hardware injected."""
import argparse
from pathlib import Path
import subprocess
import tempfile
p=argparse.ArgumentParser(description=__doc__);p.add_argument('candidate',type=Path);a=p.parse_args()
fixture=r'''
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
typedef int INT32;typedef uint32_t UINT32;typedef unsigned long ULONG;
#define NDIS_STATUS_SUCCESS 0
#define NDIS_STATUS_FAILURE 1
#define MCU_INIT 0
#define MT_INT_MASK_CSR 1
#define ARB_SCR 2
#define MT_ARB_SCR_TXDIS 1u
#define MT_ARB_SCR_RXDIS 2u
struct sender {unsigned messages;};
typedef struct {struct {unsigned flags;} MCUCtrl;struct {unsigned long peer_serial;} wr_iot_boot_ticket;struct sender wr_iot_mcu_sender_owner;unsigned wr_iot_boot_frozen,wr_iot_boot_failed,wr_iot_boot_rx_state,wr_iot_boot_ctrl_state,wr_iot_boot_ring_stage,wr_iot_boot_ring_busy,wr_iot_boot_ring_failed,wr_iot_boot_mcu_only;unsigned ledger[5];int wr_iot_transition_lock,wr_iot_mcu_sender_lock;} RTMP_ADAPTER;
static unsigned fault,held,context,initialized,joined,late_checks;
#define in_atomic() 0
#define irqs_disabled() 0
#define OS_TEST_BIT(bit,p) ((void)(bit),*(p)&1)
#define RTMP_IRQ_LOCK(l,f) do{(void)(l);(f)=0;assert(!held);held=1;}while(0)
#define RTMP_IRQ_UNLOCK(l,f) do{(void)(l);(void)(f);assert(held==1);held=0;}while(0)
#define RTMP_SPIN_LOCK_IRQSAVE(l,f) do{(void)(l);*(f)=0;assert(held==1);held=2;}while(0)
#define RTMP_SPIN_UNLOCK_IRQRESTORE(l,f) do{(void)(l);(void)(f);assert(held==2);held=1;}while(0)
static int wr_iot_mcu_boot_peer_matches(RTMP_ADAPTER *ad,unsigned long serial){assert(ad&&!held);return serial==1&&context;}
static int wr_iot_mcu_boot_context_matches(RTMP_ADAPTER *ad,void *t){assert(held==2&&t==&ad->wr_iot_boot_ticket);if(fault==11&&ad->wr_iot_boot_mcu_only&&++late_checks==2)return 0;return context&&!ad->wr_iot_boot_failed;}
static int wr_iot_mcu_boot_frozen_owned(RTMP_ADAPTER *ad){assert(!held);return context&&!ad->wr_iot_boot_failed&&ad->wr_iot_boot_frozen&&!ad->wr_iot_mcu_sender_owner.messages;}
static int wr_iot_mcu_sender_drained(struct sender *s){assert(held==2);return !s->messages;}
static unsigned rd(unsigned reg){assert(!held);if(reg==0x1134)return fault==1?2:1;if(reg==1)return fault==4||(fault==9&&initialized)?1:0;assert(reg==2);return 3;}
#define RTMP_IO_READ32(ad,reg,out) ((void)(ad),*(out)=rd(reg))
static int wr_iot_mcu_dma_disabled_idle(RTMP_ADAPTER *ad){assert(ad&&!held);return fault!=8;}
INT32 wr_iot_mcu_boot_rx_restart(RTMP_ADAPTER *);
INT32 wr_iot_mcu_boot_rx_restart_owned(RTMP_ADAPTER *);
static int wr_iot_nettask_boot_rx_restart(RTMP_ADAPTER *ad){
 assert(!held&&wr_iot_mcu_boot_rx_restart_owned(ad));initialized++;
 if(fault==5)assert(wr_iot_mcu_boot_rx_restart(ad)==1&&!ad->wr_iot_boot_failed);
 if(fault==2)return 1;
 ad->wr_iot_boot_mcu_only=1;if(fault==3||fault==10)context=0;
 return 0;
}
static int RtmpNetTaskExit(RTMP_ADAPTER *ad){assert(!held&&ad->wr_iot_boot_mcu_only&&ad->wr_iot_boot_failed);joined++;if(fault==10)return 1;ad->wr_iot_boot_mcu_only=0;return 0;}
'''+(a.candidate/'include/wr-iot-mcu-boot-rx-restart.inc').read_text()+r'''
int main(void){
 for(fault=0;fault<=12;fault++){
  RTMP_ADAPTER ad={0};held=initialized=joined=late_checks=0;context=1;
  ad.MCUCtrl.flags=1;ad.wr_iot_boot_ticket.peer_serial=1;ad.wr_iot_boot_frozen=1;
  ad.wr_iot_boot_ring_stage=4;ad.wr_iot_boot_ctrl_state=2;
  for(unsigned i=0;i<5;i++)ad.ledger[i]=100+i;
  if(fault==6)ad.wr_iot_boot_ctrl_state=1;
  if(fault==7)ad.wr_iot_boot_rx_state=2;
  if(fault==12)ad.wr_iot_mcu_sender_owner.messages=1;
  unsigned success=fault==0||fault==5;
  unsigned refused=fault==1||fault==4||fault==6||fault==7||fault==8||fault==12;
  assert(wr_iot_mcu_boot_rx_restart(&ad)==(success?0:1)&&!held);
  for(unsigned i=0;i<5;i++)assert(ad.ledger[i]==100+i);
  assert(ad.wr_iot_boot_frozen&&ad.MCUCtrl.flags==1);
  if(refused){assert(!initialized&&!joined&&!ad.wr_iot_boot_failed);continue;}
  assert(initialized==1&&ad.wr_iot_boot_rx_state==(success?2u:3u));
  assert(ad.wr_iot_boot_failed==(unsigned)!success);
  if(success)assert(ad.wr_iot_boot_mcu_only&&!joined);
  else if(fault==2)assert(!ad.wr_iot_boot_mcu_only&&!joined);
  else assert(joined==1&&ad.wr_iot_boot_mcu_only==(fault==10?1u:0u));
  assert(wr_iot_mcu_boot_rx_restart(&ad)==1&&initialized==1);
 }
 puts("PASS actual frozen MCU RX restart: exact stages/lease, nested/duplicate refusal, ROM/IRQ/DMA gates, post-init/final context loss and failed join retention; ledger/constructor fence preserved, hardware/tasklet actor injected");
}
'''
with tempfile.TemporaryDirectory(prefix='wr-mcu-rx-restart-') as td:
 c=Path(td)/'check.c';c.write_text(fixture)
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-pie','-no-pie',str(c),'-o',td+'/check'],check=True)
 subprocess.run([td+'/check'],check=True)
