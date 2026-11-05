#!/usr/bin/env python3
"""Exercise the actual retired-ID boundary with its ownership and PSE gates."""
import argparse
from pathlib import Path
import subprocess
import tempfile

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('candidate', type=Path)
a=p.parse_args()
body=(a.candidate/'include/wr-iot-mcu-boot-retired-boundary.inc').read_text()
prefix=r'''
#include <assert.h>
#include <stdio.h>
#include <string.h>
typedef int INT32; typedef unsigned long ULONG;
#define NDIS_STATUS_SUCCESS 0
#define NDIS_STATUS_FAILURE 1
#define MCU_INIT 0
#define fRTMP_ADAPTER_NIC_NOT_EXIST 1u
#define fRTMP_ADAPTER_RESET_IN_PROGRESS 2u
#define fRTMP_ADAPTER_HALT_IN_PROGRESS 4u
struct wr_iot_mcu_boot_ticket { unsigned long peer_serial,radio_serial,radio_epoch,close_serial,close_epoch; };
struct seq { unsigned occupied,cursor,poisoned,quarantined,retired; };
typedef struct { unsigned flags; } MCU;
typedef struct {
 unsigned wr_iot_boot_frozen,wr_iot_boot_hw_state,wr_iot_boot_hw_stage;
 unsigned wr_iot_boot_ring_stage,wr_iot_boot_ring_busy,wr_iot_boot_ring_failed;
 unsigned wr_iot_boot_ctrl_state,wr_iot_boot_rx_state,wr_iot_boot_irq_state;
 unsigned wr_iot_boot_dma_state,wr_iot_boot_irq_unmask_state,wr_iot_boot_epoch_done;
 unsigned wr_iot_boot_mcu_only,wr_iot_boot_rom_kind,wr_iot_boot_epoch_retired_mask;
 unsigned long wr_iot_boot_rom_peer_serial,wr_iot_boot_rom_radio_serial,wr_iot_boot_rom_radio_epoch;
 unsigned long wr_iot_boot_epoch_radio_serial,wr_iot_boot_epoch_radio_epoch;
 MCU MCUCtrl; struct {unsigned messages;} wr_iot_mcu_sender_owner; struct seq wr_iot_sequence;
 int wr_iot_transition_lock,wr_iot_mcu_sender_lock; unsigned flags;
 struct wr_iot_mcu_boot_ticket ticket;
} RTMP_ADAPTER;
static unsigned held, pse_ok, peer_ok, drift_after_pse;
#define in_atomic() 0
#define irqs_disabled() 0
#define OS_TEST_BIT(bit,p) ((void)(bit),(*(p)&1))
#define RTMP_TEST_FLAG(ad,f) ((ad)->flags&(f))
#define RTMP_IRQ_LOCK(l,f) do{(void)(l);(f)=0;assert(!held);held=1;}while(0)
#define RTMP_IRQ_UNLOCK(l,f) do{(void)(l);(void)(f);assert(held==1);held=0;}while(0)
#define RTMP_SPIN_LOCK_IRQSAVE(l,f) do{(void)(l);*(f)=0;assert(held==1);held=2;}while(0)
#define RTMP_SPIN_UNLOCK_IRQRESTORE(l,f) do{(void)(l);(void)(f);assert(held==2);held=1;}while(0)
static int wr_iot_mcu_boot_context_matches(RTMP_ADAPTER *ad,const struct wr_iot_mcu_boot_ticket *t)
{ assert(held==2); return peer_ok&&!memcmp(t,&ad->ticket,sizeof(*t)); }
static int wr_iot_mcu_boot_peer_matches(RTMP_ADAPTER *ad,unsigned long p)
{ assert(!held); return peer_ok&&p==ad->ticket.peer_serial; }
static int wr_iot_mcu_sender_drained(void *s) { assert(s&&held==2);return 1; }
static int wr_iot_mcu_boot_pse_empty(RTMP_ADAPTER *ad)
{ assert(ad&&!held);if(drift_after_pse)ad->ticket.radio_epoch++;return pse_ok; }
'''
suffix=r'''
static RTMP_ADAPTER valid(void)
{
 RTMP_ADAPTER a={0};
 a.ticket=(struct wr_iot_mcu_boot_ticket){1,2,3,4,5};
 a.wr_iot_boot_frozen=1;a.wr_iot_boot_hw_state=1;a.wr_iot_boot_hw_stage=1;
 a.wr_iot_boot_ring_stage=4;a.wr_iot_boot_rom_kind=1;
 a.wr_iot_boot_rom_peer_serial=1;a.wr_iot_boot_rom_radio_serial=2;a.wr_iot_boot_rom_radio_epoch=3;
 a.wr_iot_sequence.retired=0xfffe;a.wr_iot_sequence.cursor=15;
 return a;
}
int main(void)
{
 unsigned failure;
 for(failure=0;failure<18;failure++){
  RTMP_ADAPTER a=valid(),before;struct wr_iot_mcu_boot_ticket t; held=0;pse_ok=1;peer_ok=1;drift_after_pse=0;t=a.ticket;
  switch(failure){
  case 1:a.wr_iot_sequence.occupied=2;break;case 2:a.wr_iot_sequence.poisoned=1;break;
  case 3:a.wr_iot_sequence.quarantined=2;break;case 4:a.wr_iot_sequence.retired=1;break;
  case 5:a.wr_iot_boot_rom_kind=0;break;case 6:a.wr_iot_boot_rom_radio_epoch++;break;
  case 7:a.wr_iot_boot_ring_stage=3;break;case 8:a.wr_iot_boot_mcu_only=1;break;
  case 9:a.MCUCtrl.flags=1;break;case 10:a.wr_iot_boot_irq_state=1;break;
  case 11:a.wr_iot_boot_dma_state=1;break;case 12:a.wr_iot_boot_epoch_done=1;break;
  case 13:a.wr_iot_mcu_sender_owner.messages=1;break;case 14:pse_ok=0;break;
  case 15:drift_after_pse=1;break;case 16:peer_ok=0;break;case 17:a.flags=1;break; }
  before=a;
  assert(wr_iot_mcu_boot_retired_boundary(&a,&t)==(failure?1:0));assert(!held);
  if(failure){ assert(!memcmp(&a.wr_iot_sequence,&before.wr_iot_sequence,sizeof(a.wr_iot_sequence)));assert(a.wr_iot_boot_epoch_done==before.wr_iot_boot_epoch_done); }
  else { assert(a.wr_iot_boot_epoch_retired_mask==0xfffe&&!a.wr_iot_sequence.retired&&!a.wr_iot_sequence.cursor&&a.wr_iot_boot_epoch_done);assert(a.wr_iot_boot_epoch_radio_serial==2&&a.wr_iot_boot_epoch_radio_epoch==3);assert(wr_iot_mcu_boot_retired_boundary(&a,&t)==1); }
 }
 puts("PASS actual retired-ID boundary: frozen ROM/PSE/ring ownership and all ledger safety gates; only retired history resets");
}
'''

def run(source, expect_ok=True):
 with tempfile.TemporaryDirectory(prefix='wr-retired-boundary-') as td:
  c=Path(td)/'check.c';c.write_text(prefix+source+suffix)
  subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-pie','-no-pie',str(c),'-o',td+'/check'],check=True)
  result=subprocess.run([td+'/check'], stdout=None if expect_ok else subprocess.DEVNULL,
                        stderr=None if expect_ok else subprocess.DEVNULL)
  assert (result.returncode==0)==expect_ok

run(body)
mutated=body.replace('ad->wr_iot_sequence.retired=0;ad->wr_iot_sequence.cursor=0;', 'ad->wr_iot_sequence.cursor=0;', 1)
assert mutated!=body
run(mutated, expect_ok=False)
print('PASS mutation check: omitting retired reset is rejected by executed assertion')
