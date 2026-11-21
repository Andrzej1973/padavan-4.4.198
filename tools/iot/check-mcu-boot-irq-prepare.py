#!/usr/bin/env python3
"""Actual IRQ software preparation with SDK masks, lock order and W1C model."""
import argparse
from pathlib import Path
import re
import subprocess
import tempfile
p=argparse.ArgumentParser(description=__doc__);p.add_argument('candidate',type=Path);a=p.parse_args()
sdk=(a.candidate/'include/mac/mac_mt/mt_mac_pci.h').read_text()
macros='\n'.join(re.findall(r'^#define\s+(?:MT_INT_R1_DONE|MT_INT_T5_DONE|MT_INT_RX_CMD|MT_INT_CMD)\s+.*$',sdk,re.M))
assert len(macros.splitlines())==4
fixture=r'''
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include "tasklet-schedule-owner.h"
typedef int INT;typedef uint32_t UINT32;typedef unsigned long ULONG;
@@MASKS@@
#define NDIS_STATUS_FAILURE 1
#define NDIS_STATUS_SUCCESS 0
#define MT_INT_MASK_CSR 1
#define MT_WPDMA_GLO_CFG 2
#define MT_INT_SOURCE_CSR 3
#define TX_DMA_EN 1u
#define RX_DMA_EN 4u
#define TX_DMA_BUSY 2u
#define RX_DMA_BUSY 8u
#define fRTMP_ADAPTER_INTERRUPT_ACTIVE 1u
typedef struct {int irq_lock,LockInterrupt,wr_iot_nettask_lock;unsigned wr_iot_boot_mcu_only,wr_iot_nettask_initializing,wr_iot_nettask_joined,wr_iot_nettask_data_joined,wr_iot_nettask_data_joining;struct wr_iot_tasklet_schedule_owner wr_iot_nettask_owner,wr_iot_nettask_data_owner;unsigned int_enable_reg,int_disable_mask,int_pending,flags,wr_iot_boot_irq_saved_enable,wr_iot_boot_irq_saved_disable,wr_iot_boot_irq_saved_pending;} RTMP_ADAPTER;
static RTMP_ADAPTER *current;static unsigned fault,held,queries,writes,regs[4];
#define in_atomic() 0
#define irqs_disabled() 0
static unsigned level(int *lock){return lock==&current->irq_lock?1:lock==&current->LockInterrupt?2:lock==&current->wr_iot_nettask_lock?3:99;}
#define RTMP_INT_LOCK(l,f) do{(f)=0;assert(level(l)==held+1);held++;}while(0)
#define RTMP_INT_UNLOCK(l,f) do{(void)(f);assert(level(l)==held);held--;}while(0)
#define RTMP_CLEAR_FLAG(ad,f) ((ad)->flags&=~(f))
static int wr_iot_mcu_boot_irq_prepare_owned(RTMP_ADAPTER *ad){assert(ad==current&&!held);queries++;return !(fault==9&&queries==2);}
static unsigned rd(unsigned reg){assert(held==3&&reg<4);if(reg==3&&fault==3)return ~0u;return regs[reg];}
static void wr(unsigned reg,unsigned val){assert(held==3);writes++;if(reg==1){assert(!val);regs[1]=fault==4?1:0;}else{assert(reg==3&&val==0x202);if(fault!=5)regs[3]&=~val;}}
#define RTMP_IO_READ32(ad,reg,out) ((void)(ad),*(out)=rd(reg))
#define RTMP_IO_WRITE32(ad,reg,val) ((void)(ad),wr(reg,val))
'''.replace('@@MASKS@@',macros)+(a.candidate/'include/wr-iot-mcu-boot-irq-prepare.inc').read_text()+r'''
int main(void){
 for(fault=0;fault<=9;fault++){
  RTMP_ADAPTER ad={0};current=&ad;held=queries=writes=0;memset(regs,0,sizeof(regs));
  ad.wr_iot_boot_mcu_only=ad.wr_iot_nettask_data_joined=1;
  wr_iot_tasklet_schedule_init(&ad.wr_iot_nettask_owner);ad.wr_iot_nettask_owner.blocked=0;
  wr_iot_tasklet_schedule_init(&ad.wr_iot_nettask_data_owner);
  ad.int_enable_reg=0xffff;ad.int_disable_mask=0x55;ad.int_pending=0x8202;ad.flags=1;regs[3]=0x10202;
  switch(fault){case 1:regs[1]=1;break;case 2:regs[2]=RX_DMA_EN;break;
   case 6:ad.wr_iot_nettask_data_owner.blocked=0;break;case 7:ad.wr_iot_boot_mcu_only=0;break;
   case 8:ad.wr_iot_nettask_owner.poisoned=1;break;}
  assert(wr_iot_nettask_boot_irq_prepare(&ad)==(fault?1:0)&&!held);
  unsigned changed=fault==0||fault==4||fault==5||fault==9;
  if(changed){assert(ad.int_enable_reg==0x202&&ad.int_disable_mask==0x202&&ad.int_pending==0x8000);
   assert(ad.wr_iot_boot_irq_saved_enable==0xffff&&ad.wr_iot_boot_irq_saved_disable==0x55&&ad.wr_iot_boot_irq_saved_pending==0x8202);
   assert(!(ad.flags&1));}
  else assert(!writes&&ad.int_enable_reg==0xffff&&ad.int_disable_mask==0x55&&ad.int_pending==0x8202);
  if(!fault||fault==9)assert(writes==2&&!regs[1]&&regs[3]==0x10000);
 }
 puts("PASS actual MCU IRQ preparation: SDK RX1/TX5 mask, irq->interrupt->lane lock order, saved state, selective W1C/pending preservation, DMA/lane/readback/owner refusal; never enables IRQ/DMA, MMIO injected");
}
'''
with tempfile.TemporaryDirectory(prefix='wr-mcu-irq-prepare-') as td:
 c=Path(td)/'check.c';c.write_text(fixture)
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(a.candidate/'include'),str(c),'-o',td+'/check'],check=True)
 subprocess.run([td+'/check'],check=True)
