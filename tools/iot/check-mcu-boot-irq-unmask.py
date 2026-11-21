#!/usr/bin/env python3
"""Actual MCU-only unmask/abort plus real tasklet IRQ rearm; hardware injected."""
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
#define ARB_SCR 4
#define MT_ARB_SCR_TXDIS 1u
#define MT_ARB_SCR_RXDIS 2u
#define MT_MAC 1
#define RTMP_MAC_PCI 1
#define fRTMP_ADAPTER_START_UP 2u
#define fRTMP_ADAPTER_RESET_IN_PROGRESS 4u
#define fRTMP_ADAPTER_HALT_IN_PROGRESS 8u
#define fRTMP_ADAPTER_NIC_NOT_EXIST 16u
#define TX_DMA_EN 1u
#define RX_DMA_EN 4u
#define TX_DMA_BUSY 2u
#define RX_DMA_BUSY 8u
#define fRTMP_ADAPTER_INTERRUPT_ACTIVE 1u
typedef struct {int irq_lock,LockInterrupt,wr_iot_nettask_lock;unsigned wr_iot_boot_mcu_only,wr_iot_nettask_initializing,wr_iot_nettask_joined,wr_iot_nettask_data_joined,wr_iot_nettask_data_joining;struct wr_iot_tasklet_schedule_owner wr_iot_nettask_owner,wr_iot_nettask_data_owner;unsigned int_enable_reg,int_disable_mask,int_pending,flags,wr_iot_boot_irq_saved_enable,wr_iot_boot_irq_saved_disable,wr_iot_boot_irq_saved_pending,wr_iot_boot_irq_unmask_state,wr_iot_boot_irq_startup_owned;} RTMP_ADAPTER;
static RTMP_ADAPTER *current;static unsigned fault,held,queries,writes,barriers,regs[5];
#define in_atomic() 0
#define irqs_disabled() 0
static unsigned level(int *lock){return lock==&current->irq_lock?1:lock==&current->LockInterrupt?2:lock==&current->wr_iot_nettask_lock?3:99;}
#define RTMP_INT_LOCK(l,f) do{(f)=0;assert(level(l)==held+1);held++;}while(0)
#define RTMP_INT_UNLOCK(l,f) do{(void)(f);assert(level(l)==held);held--;}while(0)
#define RTMP_CLEAR_FLAG(ad,f) ((ad)->flags&=~(f))
#define RTMP_SET_FLAG(ad,f) ((ad)->flags|=(f))
#define RTMP_TEST_FLAG(ad,f) ((ad)->flags&(f))
#define wmb() (barriers++)
static int wr_iot_mcu_boot_irq_unmask_owned(RTMP_ADAPTER *ad){assert(ad==current&&!held&&ad->wr_iot_boot_irq_unmask_state==1);queries++;return fault!=9;}
static unsigned rd(unsigned reg){assert(held==3&&reg<5);if(reg==2&&fault==3)return ~0u;return regs[reg];}
static void wr(unsigned reg,unsigned val){assert(held==3&&reg==1);writes++;
 if(val){assert(val==0x202&&barriers==1&&(current->flags&3)==3);regs[1]=fault==4?val^2:val;}
 else {assert(current->wr_iot_nettask_owner.blocked);regs[1]=fault==10?1:0;}}
#define RTMP_IO_READ32(ad,reg,out) ((void)(ad),*(out)=rd(reg))
#define RTMP_IO_WRITE32(ad,reg,val) ((void)(ad),wr(reg,val))
'''.replace('@@MASKS@@',macros)+(a.candidate/'include/wr-iot-mcu-boot-irq-unmask.inc').read_text()
net=(a.candidate/'os/linux/rt_rbus_pci_drv.c').read_text()
start=net.index('static inline void rt2860_int_enable(');end=net.index('\n}',start)+2
fixture+=r'''
#undef RTMP_INT_LOCK
#undef RTMP_INT_UNLOCK
#define RTMP_INT_LOCK(l,f) do{(f)=0;assert((l)==&current->wr_iot_nettask_lock&&!held);held=3;}while(0)
#define RTMP_INT_UNLOCK(l,f) do{(void)(f);assert((l)==&current->wr_iot_nettask_lock&&held==3);held=0;}while(0)
'''+net[start:end]+r'''
int main(void){
 for(fault=0;fault<=10;fault++){
  RTMP_ADAPTER ad={0};current=&ad;held=queries=writes=barriers=0;memset(regs,0,sizeof(regs));
  ad.wr_iot_boot_irq_unmask_state=1;ad.wr_iot_boot_mcu_only=ad.wr_iot_nettask_data_joined=1;
  wr_iot_tasklet_schedule_init(&ad.wr_iot_nettask_owner);ad.wr_iot_nettask_owner.blocked=0;
  wr_iot_tasklet_schedule_init(&ad.wr_iot_nettask_data_owner);
  ad.int_enable_reg=ad.int_disable_mask=0x202;ad.int_pending=0x8000;regs[2]=TX_DMA_EN|RX_DMA_EN|RX_DMA_BUSY;regs[4]=3;
  switch(fault){case 1:regs[1]=1;break;case 2:regs[2]=RX_DMA_EN;break;
   case 5:ad.wr_iot_nettask_data_owner.blocked=0;break;case 6:ad.int_enable_reg=0xffff;break;
   case 7:ad.int_pending|=2;break;case 8:ad.flags=fRTMP_ADAPTER_HALT_IN_PROGRESS;break;}
  unsigned success=fault==0||fault==10;
  assert(wr_iot_nettask_boot_irq_unmask(&ad)==(success?0:1)&&!held);
  if(success)assert(writes==1&&regs[1]==0x202&&(ad.flags&3)==3&&!ad.int_disable_mask);
  else if(fault!=4)assert(!writes&&!ad.wr_iot_boot_irq_startup_owned);
  assert(wr_iot_nettask_boot_irq_abort(&ad)==(fault==10?1:0)&&!held);
  assert(ad.wr_iot_nettask_owner.blocked&&(ad.int_disable_mask&0x202)==0x202&&!ad.wr_iot_boot_irq_startup_owned&&!(ad.flags&3));
  assert(ad.int_pending==(fault==7?0x8002u:0x8000u));
  unsigned previous=writes;rt2860_int_enable(&ad,0x202);assert(writes==previous&&!held&&(ad.int_disable_mask&0x202)==0x202);
 }
 puts("PASS actual MCU IRQ unmask/abort and actual tasklet rearm: exact mask, flags-before-write, DMA/MAC/lane/readback refusal, selective pending preservation and blocked late reenable; MMIO injected");
}
'''
with tempfile.TemporaryDirectory(prefix='wr-mcu-irq-unmask-') as td:
 c=Path(td)/'check.c';c.write_text(fixture)
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(a.candidate/'include'),str(c),'-o',td+'/check'],check=True)
 subprocess.run([td+'/check'],check=True)
