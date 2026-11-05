#!/usr/bin/env python3
"""Execute actual boot-open core helpers + ioctl dispatch; DMA/reserve injected."""
import argparse
from pathlib import Path
import subprocess
import tempfile
p=argparse.ArgumentParser(description=__doc__);p.add_argument('candidate',type=Path);a=p.parse_args()
fixture=r'''
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "peer-open-owner.h"
#include "peer-close-executor.h"
#include "peer-open-request.h"
#include "tasklet-schedule-owner.h"
#include "mcu-sender-owner.h"
#include "mcu-boot-ticket.h"
typedef int INT;typedef unsigned int UINT;typedef unsigned long ULONG;
#define MT7603 1
#define RTMP_PCI_SUPPORT 1
#define NDIS_STATUS_SUCCESS 0
#define NDIS_STATUS_FAILURE 1
#define HIF_MT 1
#define MCU_INIT 0
#define OS_TEST_BIT(bit,p) ((void)(bit),*(p)&1)
#define MAX_LEN_OF_MAC_TABLE 4
#define MAX_LEN_OF_TR_TABLE 3
#define IS_ENTRY_NONE(e) (!(e)->kind)
typedef struct {
 int MacTabLock,wr_iot_nettask_lock,wr_iot_mcu_sender_lock,is7603;
 void *net_dev;struct {int hif_type;} chipCap;struct {unsigned flags;} MCUCtrl;
 unsigned wr_iot_peer_delete_active,wr_iot_peer_legacy_close_state;
 struct {unsigned Size;struct {int kind;} Content[4];struct {int wr_iot_setup_observed,wr_iot_setup_result;} tr_entry[3];} MacTab;
 struct wr_iot_peer_open_owner wr_iot_peer_open_owner;
 struct wr_iot_peer_table_owner wr_iot_peer_table_owner;
 struct wr_iot_peer_close_executor wr_iot_peer_close_executor;
 struct wr_iot_mcu_sender_owner wr_iot_mcu_sender_owner;
 struct wr_iot_mcu_boot_ticket wr_iot_boot_ticket;
 unsigned wr_iot_boot_active,wr_iot_boot_failed,wr_iot_boot_mcu_only;
 unsigned wr_iot_nettask_initializing,wr_iot_nettask_joined,wr_iot_nettask_data_joined,wr_iot_nettask_data_joining;
 struct wr_iot_tasklet_schedule_owner wr_iot_nettask_owner,wr_iot_nettask_data_owner;
} RTMP_ADAPTER;
static unsigned held,reserves,dma_ready,dma_reads;
#define IS_MT7603(ad) ((ad)->is7603)
#define NdisAcquireSpinLock(l) do{(void)(l);assert(!held);held=1;}while(0)
#define NdisReleaseSpinLock(l) do{(void)(l);assert(held);held=0;}while(0)
#define RTMP_INT_LOCK(l,f) do{(void)(l);(f)=0;assert(!held);held=1;}while(0)
#define RTMP_INT_UNLOCK(l,f) do{(void)(l);(void)(f);assert(held);held=0;}while(0)
#define RTMP_SPIN_LOCK_IRQSAVE(l,f) do{(void)(l);*(f)=0;assert(!held);held=1;}while(0)
#define RTMP_SPIN_UNLOCK_IRQRESTORE(l,f) do{(void)(l);(void)(f);assert(held);held=0;}while(0)
INT wr_iot_mcu_boot_reserve(RTMP_ADAPTER *ad,unsigned long serial,struct wr_iot_mcu_boot_ticket *out){assert(!held&&serial==1);reserves++;ad->wr_iot_boot_active=1;ad->wr_iot_boot_ticket.peer_serial=serial;*out=ad->wr_iot_boot_ticket;return 0;}
static int wr_iot_mcu_dma_disabled_idle(RTMP_ADAPTER *ad){assert(ad&&!held);dma_reads++;return dma_ready;}
'''+(a.candidate/'include/wr-iot-mcu-boot-open.inc').read_text()+'\n'+(a.candidate/'include/wr-iot-peer-open-dispatch.inc').read_text()+r'''
static void fresh(RTMP_ADAPTER *ad){
 memset(ad,0,sizeof(*ad));ad->net_dev=ad;ad->is7603=ad->chipCap.hif_type=1;
 wr_iot_mcu_sender_init(&ad->wr_iot_mcu_sender_owner);
 wr_iot_tasklet_schedule_init(&ad->wr_iot_nettask_owner);wr_iot_tasklet_schedule_init(&ad->wr_iot_nettask_data_owner);
 ad->wr_iot_nettask_joined=ad->wr_iot_nettask_data_joined=1;
 wr_iot_peer_open_owner_init(&ad->wr_iot_peer_open_owner);wr_iot_peer_table_owner_init(&ad->wr_iot_peer_table_owner);
 struct wr_iot_peer_open_ticket t;
 assert(wr_iot_peer_open_begin(&ad->wr_iot_peer_open_owner,&ad->wr_iot_peer_table_owner,ad,1,&t)&&t.serial==1);
 reserves=dma_reads=0;dma_ready=1;
}
int main(void){
 RTMP_ADAPTER ad;fresh(&ad);
 struct wr_iot_peer_open_request req={1,WR_PEER_OPEN_BOOT_PREPARE,&ad,1};
 assert(!wr_iot_peer_open_dispatch(&ad,&req,sizeof req)&&!reserves&&!ad.wr_iot_boot_active);
 req.serial=2;assert(wr_iot_peer_open_dispatch(&ad,&req,sizeof req)==1);req.serial=1;
 ad.wr_iot_mcu_sender_owner.closed=1;assert(wr_iot_peer_open_dispatch(&ad,&req,sizeof req)==1&&!reserves);
 ad.wr_iot_mcu_sender_owner.release_claimed=ad.wr_iot_mcu_sender_owner.off_done=1;
#ifdef LOAD_FW_ONE_TIME
 assert(wr_iot_peer_open_dispatch(&ad,&req,sizeof req)==1&&!reserves);
#else
 assert(!wr_iot_peer_open_dispatch(&ad,&req,sizeof req)&&reserves==1&&ad.wr_iot_boot_active);
#endif
 for(unsigned fault=0;fault<16;fault++){
  fresh(&ad);ad.wr_iot_boot_active=1;ad.wr_iot_boot_ticket.peer_serial=1;
  ad.wr_iot_mcu_sender_owner.closed=ad.wr_iot_mcu_sender_owner.release_claimed=ad.wr_iot_mcu_sender_owner.uncertain=1;
  req=(struct wr_iot_peer_open_request){1,WR_PEER_OPEN_BOOT_IRQ_READY,&ad,1};
  if(fault==1)ad.MCUCtrl.flags=1;
  if(fault==2)ad.wr_iot_boot_mcu_only=1;
  if(fault==3)ad.wr_iot_nettask_initializing=1;
  if(fault==4)ad.wr_iot_nettask_joined=0;
  if(fault==5)ad.wr_iot_nettask_data_joined=0;
  if(fault==6)ad.wr_iot_nettask_data_joining=1;
  if(fault==7)ad.wr_iot_nettask_owner.blocked=0;
  if(fault==8)ad.wr_iot_nettask_data_owner.blocked=0;
  if(fault==9)ad.wr_iot_mcu_sender_owner.messages=1;
  if(fault==10)ad.wr_iot_mcu_sender_owner.inflight=1;
  if(fault==11)ad.wr_iot_mcu_sender_owner.radio_active=1;
  if(fault==12)ad.wr_iot_mcu_sender_owner.off_active=1;
  if(fault==13)dma_ready=0;
  if(fault==14)req.serial=2;
  if(fault==15)ad.wr_iot_peer_open_owner.phase=WR_PEER_OPEN_RETAINED;
  assert(wr_iot_peer_open_dispatch(&ad,&req,sizeof req)==(fault?1:0)&&!held);
  assert(ad.wr_iot_mcu_sender_owner.uncertain&&ad.wr_iot_mcu_sender_owner.release_claimed);
 }
 fresh(&ad);ad.wr_iot_peer_open_owner.phase=WR_PEER_OPEN_IDLE;
 assert(!wr_iot_boot_open_irq_ready(&ad,1)); /* Ordinary path unaffected. */
 puts("PASS actual core boot-open/dispatch: cold vs retained close, exact peer identity, join/controller/message/DMA gates and uncertainty preserved; reserve and DMA injected");
}
'''
with tempfile.TemporaryDirectory(prefix='wr-mcu-boot-open-core-') as td:
 c=Path(td)/'check.c';c.write_text(fixture)
 for once in (False,True):
  cmd=['gcc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(a.candidate/'include'),str(c),'-o',td+'/check']
  if once:cmd.insert(1,'-DLOAD_FW_ONE_TIME=1')
  subprocess.run(cmd,check=True);subprocess.run([td+'/check'],check=True)
