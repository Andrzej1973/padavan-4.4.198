#!/usr/bin/env python3
"""Exercise actual known-PSE-queue snapshot with SDK masks and injected MMIO."""
import argparse
from pathlib import Path
import subprocess
import tempfile
p=argparse.ArgumentParser(description=__doc__);p.add_argument('candidate',type=Path);a=p.parse_args()
fixture=r'''
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include "mac/mac_mt/pse.h"
#define BIT8 (1u<<8)
#define BIT9 (1u<<9)
#include "mac/mac_mt/wf_arb.h"
#include "tasklet-schedule-owner.h"
typedef uint32_t UINT32;typedef unsigned long ULONG;typedef int BOOLEAN;typedef int INT;
#define TRUE 1
#define FALSE 0
#define HIF_MT 1
#define MCU_INIT 0
#define TOP_MISC2 1
#define MT_INT_MASK_CSR 2
#define MT_WPDMA_GLO_CFG 3
#define TX_DMA_EN 1u
#define RX_DMA_EN 4u
#define TX_DMA_BUSY 2u
#define RX_DMA_BUSY 8u
#define fRTMP_ADAPTER_NIC_NOT_EXIST 1u
typedef struct {int IndirectUpdateLock,wr_iot_nettask_lock;struct {int hif_type;} chipCap;struct {unsigned flags;} MCUCtrl;unsigned flags,wr_iot_nettask_joined,wr_iot_nettask_data_joined,wr_iot_boot_mcu_only,wr_iot_nettask_initializing,wr_iot_nettask_data_joining;struct wr_iot_tasklet_schedule_owner wr_iot_nettask_owner,wr_iot_nettask_data_owner;} RTMP_ADAPTER;
#define IS_MT7603(ad) ((void)(ad),1)
#define OS_TEST_BIT(bit,p) ((void)(bit),*(p)&1)
#define RTMP_TEST_FLAG(ad,flag) ((ad)->flags&(flag))
#define in_atomic() 0
#define irqs_disabled() 0
static unsigned held,mode,queries,restores,selector,original,context,seen[21];static int nonempty;
#define NdisAcquireSpinLock(l) do{(void)(l);assert(!held);held=1;}while(0)
#define NdisReleaseSpinLock(l) do{(void)(l);assert(held);held=0;}while(0)
#define RTMP_INT_LOCK(l,f) do{(void)(l);(f)=0;assert(!held);held=1;}while(0)
#define RTMP_INT_UNLOCK(l,f) do{(void)(l);(void)(f);assert(held);held=0;}while(0)
static int wr_iot_mcu_boot_frozen_owned(RTMP_ADAPTER *ad){assert(ad&&!held);return context;}
static int queue_index(void){unsigned pid=GET_PID(selector),qid=GET_QID(selector);return pid==0&&qid<3?(int)qid:pid==1&&qid<4?(int)(3+qid):pid==2&&qid<14?(int)(7+qid):-1;}
static unsigned read_register(unsigned reg){
 if(reg==TOP_MISC2)return mode==1?2:1;
 if(reg==ARB_SCR)return mode==2?0:MT_ARB_SCR_TXDIS|MT_ARB_SCR_RXDIS;
 if(reg==MT_INT_MASK_CSR)return mode==3?1:0;
 if(reg==MT_WPDMA_GLO_CFG)return mode==4?TX_DMA_EN:0;
 assert(held);
 if(reg==GC)return mode==5?0:mode==6?~0u:PSE_INIT_DONE;
 if(reg==FC_SP0P1)return mode==7?1:mode==8?(1u<<16):0;
 if(reg==FC_SP2Q0Q1)return mode==9?1:mode==10?(1u<<16):0;
 if(reg==FC_SP2Q2)return mode==11?1:0;
 assert(reg==C_GFF);
 int index=queue_index();
 if(index<0)return selector|0xfff;
 queries++;seen[index]++;
 if(mode==12)return ~0u;
 if(mode==13)return (selector^(1u<<16))|0xfff;
 return selector|(index==nonempty?123u:0xfffu);
}
static void write_register(unsigned reg,unsigned value){
 assert(held&&reg==C_GFF);selector=value&(GET_PID_MASK|GET_QID_MASK|GET_RVSE_MASK);
 if(queue_index()<0){restores++;if(mode==14)selector^=1u<<16;}
}
#define RTMP_IO_READ32(ad,reg,out) ((void)(ad),*(out)=read_register(reg))
#define RTMP_IO_WRITE32(ad,reg,val) ((void)(ad),write_register(reg,val))
static void delay(unsigned value){assert(!held&&value==1000);if(mode==15&&queries==21)context=0;}
#define RtmpusecDelay delay
'''+(a.candidate/'include/wr-iot-mcu-dma-disabled-idle.inc').read_text()+'\n'+(a.candidate/'include/wr-iot-mcu-boot-pse-empty.inc').read_text()+r'''
static void fresh(RTMP_ADAPTER *ad){
 memset(ad,0,sizeof(*ad));ad->chipCap.hif_type=1;ad->wr_iot_nettask_joined=ad->wr_iot_nettask_data_joined=1;
 wr_iot_tasklet_schedule_init(&ad->wr_iot_nettask_owner);wr_iot_tasklet_schedule_init(&ad->wr_iot_nettask_data_owner);
 original=selector=SET_GET_PID(2)|SET_GET_QID(31)|GET_RVSE_MASK;context=1;
 queries=restores=0;memset(seen,0,sizeof(seen));nonempty=-1;
}
int main(void){
 RTMP_ADAPTER ad;
 for(mode=0;mode<=15;mode++){
  fresh(&ad);assert(wr_iot_mcu_boot_pse_empty(&ad)==(mode?0:1)&&!held);
  if(!mode){assert(queries==42&&restores==2&&selector==original);for(unsigned i=0;i<21;i++)assert(seen[i]==2);}
  if(mode!=14)assert(selector==original);
  assert(queries<=42);
 }
 mode=0;
 for(int queue=0;queue<21;queue++){
  fresh(&ad);nonempty=queue;
  assert(!wr_iot_mcu_boot_pse_empty(&ad)&&queries==(unsigned)queue+1&&restores==1&&selector==original&&!held);
 }
 fresh(&ad);ad.MCUCtrl.flags=1;assert(!wr_iot_mcu_boot_pse_empty(&ad)&&!queries);
 fresh(&ad);ad.wr_iot_nettask_joined=0;assert(!wr_iot_mcu_boot_pse_empty(&ad)&&!queries);
 fresh(&ad);ad.wr_iot_boot_mcu_only=1;assert(!wr_iot_mcu_boot_pse_empty(&ad)&&!queries);
 mode=0;fresh(&ad);assert(wr_iot_boot_pse_snapshot(&ad)==1);
 for(mode=7;mode<=11;mode++){fresh(&ad);assert(wr_iot_boot_pse_snapshot(&ad)==0);}
 for(unsigned i=0;i<5;i++){mode=(unsigned[]){5,6,12,13,14}[i];fresh(&ad);assert(wr_iot_boot_pse_snapshot(&ad)==-1);}
 puts("PASS actual SDK PSE snapshot: all21 queues, used-page gates, two sweeps, selector restore, bus/mismatch failures and context drift; MMIO injected, no queue removal/epoch proof");
}
'''
with tempfile.TemporaryDirectory(prefix='wr-mcu-boot-pse-empty-') as td:
 c=Path(td)/'check.c';c.write_text(fixture)
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(a.candidate/'include'),str(c),'-o',td+'/check'],check=True)
 subprocess.run([td+'/check'],check=True)
