#!/usr/bin/env python3
"""Actual checked PCI initializer and wrapper; OS/queue/owner operations injected."""
import argparse
from pathlib import Path
import subprocess
import tempfile
p=argparse.ArgumentParser(description=__doc__);p.add_argument('candidate',type=Path);a=p.parse_args()
fixture=r'''
#include <assert.h>
#include <string.h>
#include <stdio.h>
typedef int INT32;typedef unsigned long ULONG;
#define NDIS_STATUS_SUCCESS 0
#define NDIS_STATUS_FAILURE 1
#define MCU_INIT 0
#define FALSE 0
#define fRTMP_ADAPTER_MCU_SEND_IN_BAND_CMD 2u
struct MCU_CTRL {unsigned flags,cmd_seq,power_on,dpd_on,RxStream0,RxStream1;int cmd_msg_task,txq_lock,rxq_lock,ackq_lock,kickq_lock,tx_doneq_lock,rx_doneq_lock;int txq,rxq,ackq,kickq,tx_doneq,rx_doneq;unsigned tx_kickout_fail_count,tx_timeout_fail_count,rx_receive_fail_count,alloc_cmd_msg,free_cmd_msg;void *ad;};
typedef struct adapter {struct MCU_CTRL MCUCtrl;unsigned flags,wr_iot_boot_ctrl_state,wr_iot_boot_ring_stage,wr_iot_boot_ring_busy,wr_iot_boot_ring_failed,wr_iot_boot_failed,wr_iot_boot_frozen;int wr_iot_transition_lock,wr_iot_mcu_sender_lock,wr_iot_boot_ticket;unsigned ledger[5];struct {void (*MCUCtrlInit)(struct adapter *);} chipOps;} RTMP_ADAPTER;
static unsigned fault,context,held,locks,queues,created,init_calls,exits,atomic_context;
#define in_atomic() atomic_context
#define irqs_disabled() 0
#define OS_TEST_BIT(bit,p) ((void)(bit),*(p)&1)
#define OS_SET_BIT(bit,p) ((void)(bit),*(p)|=1)
#define RTMP_CLEAR_FLAG(ad,f) ((ad)->flags&=~(f))
#define RTMP_IRQ_LOCK(l,f) do{(void)(l);(f)=0;assert(!held);held=1;}while(0)
#define RTMP_IRQ_UNLOCK(l,f) do{(void)(l);(void)(f);assert(held==1);held=0;}while(0)
#define RTMP_SPIN_LOCK_IRQSAVE(l,f) do{(void)(l);*(f)=0;assert(held==1);held=2;}while(0)
#define RTMP_SPIN_UNLOCK_IRQRESTORE(l,f) do{(void)(l);(void)(f);assert(held==2);held=1;}while(0)
static void AndesCtrlInit(RTMP_ADAPTER *ad){(void)ad;assert(0);}
static int wr_iot_mcu_boot_pse_empty(RTMP_ADAPTER *ad){assert(!held);return context&&!ad->MCUCtrl.flags;}
static int wr_iot_mcu_boot_context_matches(RTMP_ADAPTER *ad,int *ticket){assert(held==2&&ticket==&ad->wr_iot_boot_ticket);return context&&!ad->wr_iot_boot_failed&&!(fault==3&&ad->MCUCtrl.flags);}
static int wr_iot_mcu_boot_frozen_owned(RTMP_ADAPTER *ad){assert(!held);return context&&ad->wr_iot_boot_frozen;}
static void AndesCmdMsgBh(unsigned long p){(void)p;}
INT32 wr_iot_mcu_boot_controller_init(RTMP_ADAPTER *ad);
static int init_task(RTMP_ADAPTER *ad,int *task,void (*fn)(unsigned long),unsigned long param){
 assert(ad&&task==&ad->MCUCtrl.cmd_msg_task&&fn==AndesCmdMsgBh&&param==(unsigned long)ad&&!held);init_calls++;
 if(fault==7){assert(wr_iot_mcu_boot_controller_init(ad)==1&&!ad->wr_iot_boot_failed);}
#if defined(OS_ABL_FUNC_SUPPORT) && !defined(WORKQUEUE_BH)
 if(fault==1)return 0;
#endif
 created++;if(fault==2)context=0;return 1;
}
#define RTMP_OS_TASKLET_INIT init_task
static RTMP_ADAPTER *current;
#define tasklet_init(task,fn,param) ((void)init_task(current,task,fn,param))
static void alloc_lock(RTMP_ADAPTER *ad,int *lock){assert(ad&&lock&&!held&&created);locks++;}
#define NdisAllocateSpinLock alloc_lock
static void AndesQueueInit(struct MCU_CTRL *ctl,int *q){assert(ctl&&q&&!held);*q=0;queues++;}
static void AndesCtrlExit(RTMP_ADAPTER *ad){assert(ad->MCUCtrl.flags&&created==1&&!held);ad->MCUCtrl.flags=0;created=0;exits++;}
'''+(a.candidate/'include/wr-iot-mcu-boot-controller-init.inc').read_text()+r'''
int main(void){
 for(fault=0;fault<=8;fault++){
  RTMP_ADAPTER ad={0};current=&ad;context=1;held=locks=queues=created=init_calls=exits=atomic_context=0;
  ad.chipOps.MCUCtrlInit=AndesCtrlInit;ad.wr_iot_boot_frozen=1;ad.wr_iot_boot_ring_stage=4;ad.MCUCtrl.cmd_seq=12;
  ad.MCUCtrl.power_on=ad.MCUCtrl.dpd_on=ad.MCUCtrl.RxStream0=ad.MCUCtrl.RxStream1=1;
  for(unsigned i=0;i<5;i++)ad.ledger[i]=100+i;
  switch(fault){case 4:ad.chipOps.MCUCtrlInit=NULL;break;case 5:ad.wr_iot_boot_ring_stage=3;break;case 6:ad.MCUCtrl.flags=1;break;case 8:atomic_context=1;break;}
  unsigned refused=fault==4||fault==5||fault==6||fault==8;
  unsigned failed=fault==2||fault==3;
#if defined(OS_ABL_FUNC_SUPPORT) && !defined(WORKQUEUE_BH)
  failed|=fault==1;
#endif
  int ret=wr_iot_mcu_boot_controller_init(&ad);assert(ret==(refused||failed?1:0)&&!held);
  for(unsigned i=0;i<5;i++)assert(ad.ledger[i]==100+i);
  if(refused){assert(!ad.wr_iot_boot_ctrl_state&&!ad.wr_iot_boot_failed&&!init_calls&&!locks);continue;}
  assert(ad.wr_iot_boot_ctrl_state==(failed?3u:2u)&&ad.wr_iot_boot_failed==failed);
  if(!failed)assert(ad.MCUCtrl.flags&&created==1&&queues==6&&locks==6&&ad.MCUCtrl.cmd_seq==0&&!ad.MCUCtrl.power_on&&!ad.MCUCtrl.dpd_on&&!ad.MCUCtrl.RxStream0&&!ad.MCUCtrl.RxStream1);
  else assert(!ad.MCUCtrl.flags&&!created);
  if(fault==2||fault==3)assert(exits==1&&queues==6);
  assert(wr_iot_mcu_boot_controller_init(&ad)==1&&init_calls==1);
 }
 puts("PASS actual checked PCI controller init: OS failure, context loss, nested/duplicate/stage refusal, queue/BH ownership and ledger preservation; OS operations injected, no IRQ/DMA/restart/runtime proof");
}
'''
for flags in ([],['-DOS_ABL_FUNC_SUPPORT'],['-DWORKQUEUE_BH']):
 with tempfile.TemporaryDirectory(prefix='wr-mcu-controller-init-') as td:
  c=Path(td)/'check.c';c.write_text(fixture)
  subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-pie','-no-pie',*flags,str(c),'-o',td+'/check'],check=True)
  subprocess.run([td+'/check'],check=True)
