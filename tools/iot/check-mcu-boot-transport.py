#!/usr/bin/env python3
"""Execute generated owned bootstrap transport API; hardware/queue ops injected."""
import argparse
from pathlib import Path
import subprocess
import tempfile
p=argparse.ArgumentParser(description=__doc__);p.add_argument('candidate',type=Path);a=p.parse_args();here=Path(__file__).resolve().parent
fixture=r'''
#include <assert.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include "radio-transition.h"
#include "mcu-sender-owner.h"
#include "mcu-boot-ticket.h"
#include "mcu-boot-result.h"
typedef int INT32;typedef unsigned long ULONG;typedef void VOID;
#define NDIS_STATUS_SUCCESS 0
#define NDIS_STATUS_FAILURE 1
#define HIF_MT 1
#define MT_FW_SCATTER 0xee
#define MT_UPLOAD_FW_UNIT 4096
#define WR_PEER_OPEN_CONFIG 1
#define MCU_INIT 0
#define OS_TEST_BIT(bit,p) ((void)(bit),*(p)&1)
#define IS_MT7603(ad) ((ad)->mt7603)
struct cmd_msg {void *priv;unsigned long wr_iot_boot_peer_serial,wr_iot_boot_radio_serial,wr_iot_boot_epoch;unsigned need_retransmit,need_wait,cmd_type,ext_cmd_type,wr_iot_checked;};
typedef struct adapter {
 int MacTabLock,wr_iot_transition_lock,wr_iot_mcu_sender_lock,wr_iot_mcu_sender_wait,mt7603;
 void *net_dev;struct {int hif_type;} chipCap;struct {unsigned flags;} MCUCtrl;
 struct {unsigned long serial;void *device;int phase;} wr_iot_peer_open_owner;
 int wr_iot_peer_close_executor;
 struct wr_iot_radio_transition wr_iot_transition;
 struct wr_iot_mcu_sender_owner wr_iot_mcu_sender_owner;
 struct wr_iot_mcu_boot_ticket wr_iot_boot_ticket;
 unsigned wr_iot_boot_active,wr_iot_boot_failed,wr_iot_boot_frozen;
 unsigned wr_iot_control_users,wr_iot_control_poisoned;
 struct {int (*pci_kick_out_cmd_msg)(struct adapter *,struct cmd_msg *);} chipOps;
} RTMP_ADAPTER;
int fake_wait(void);
#define msecs_to_jiffies(n) (n)
#define wait_event_timeout(q,c,t) ((void)(q),assert((t)==5000),fake_wait()?(c):0)
static unsigned held;static int atomic_context,alloc_fail,sent,refused,transport_result,nest;
#define in_atomic() (atomic_context)
#define irqs_disabled() 0
#define NdisAcquireSpinLock(l) do{(void)(l);assert(!held);held=4;}while(0)
#define NdisReleaseSpinLock(l) do{(void)(l);assert(held==4);held=0;}while(0)
#define RTMP_IRQ_LOCK(l,f) do{(void)(l);(f)=0;assert(!held);held=1;}while(0)
#define RTMP_IRQ_UNLOCK(l,f) do{(void)(l);(void)(f);assert(held==1);held=0;}while(0)
#define RTMP_SPIN_LOCK_IRQSAVE(l,f) do{(void)(l);*(f)=0;assert(!(held&2));held|=2;}while(0)
#define RTMP_SPIN_UNLOCK_IRQRESTORE(l,f) do{(void)(l);(void)(f);assert(held&2);held&=~2u;}while(0)
#define wake_up_all(q) ((void)(q),assert(held&2))
static int wr_iot_peer_close_executor_idle(int *s){assert(held==4);return !*s;}
static void wr_iot_mcu_message_drop(RTMP_ADAPTER *ad,unsigned slot,unsigned uncertain){
 (void)slot;(void)uncertain;assert(!held);assert(wr_iot_mcu_message_leave(&ad->wr_iot_mcu_sender_owner));
}
static struct cmd_msg *wr_iot_mcu_alloc_body(RTMP_ADAPTER *ad,unsigned len){
 (void)len;assert(!held&&ad->wr_iot_mcu_sender_owner.messages);
 if(alloc_fail)return NULL;
 struct cmd_msg *m=calloc(1,sizeof(*m));assert(m);m->priv=ad;return m;
}
static void AndesForceFreeCmdMsg(struct cmd_msg *m){assert(!held);RTMP_ADAPTER *ad=m->priv;free(m);refused++;wr_iot_mcu_message_drop(ad,0,0);}
static int AndesMTPciKickOutCmdMsg(RTMP_ADAPTER *ad,struct cmd_msg *m){(void)ad;(void)m;return 0;}
INT32 wr_iot_mcu_boot_send(RTMP_ADAPTER *,struct cmd_msg *,const struct wr_iot_mcu_boot_ticket *);
struct cmd_msg *wr_iot_mcu_boot_alloc(RTMP_ADAPTER *,unsigned,const struct wr_iot_mcu_boot_ticket *);
static INT32 wr_iot_mcu_send_body(RTMP_ADAPTER *ad,struct cmd_msg *m){
 assert(!held&&ad->wr_iot_mcu_sender_owner.inflight==1&&ad->wr_iot_mcu_sender_owner.radio_active);
 assert(m->wr_iot_checked==m->need_wait);sent++;
 if(nest){nest=0;struct cmd_msg *other=wr_iot_mcu_boot_alloc(ad,0,&ad->wr_iot_boot_ticket);assert(other);
  other->cmd_type=1;other->need_wait=1;
  assert(wr_iot_mcu_boot_send(ad,other,&ad->wr_iot_boot_ticket)==1);
 }
 free(m);wr_iot_mcu_message_drop(ad,0,0);return transport_result;
}
'''+(a.candidate/'include/wr-iot-mcu-boot-transport.inc').read_text()+r'''
static RTMP_ADAPTER *wait_ad;static struct cmd_msg *parked;static int wait_mode;
int fake_wait(void){
 assert(!held&&wait_ad&&wait_ad->wr_iot_boot_frozen);
 assert(!wr_iot_mcu_boot_alloc(wait_ad,0,&wait_ad->wr_iot_boot_ticket));
 if(wait_mode==1)return 0;
 if(parked){AndesForceFreeCmdMsg(parked);parked=NULL;}
 if(wait_mode==2)wait_ad->wr_iot_transition.epoch++;
 return 1;
}
static void init(RTMP_ADAPTER *ad){
 memset(ad,0,sizeof(*ad));ad->mt7603=ad->chipCap.hif_type=1;ad->net_dev=ad;
 wr_iot_radio_transition_init(&ad->wr_iot_transition);
 ad->wr_iot_transition.busy=WR_RADIO_START;ad->wr_iot_transition.serial=8;
 ad->wr_iot_transition.epoch=10;ad->wr_iot_transition.retired_serial=7;
 ad->wr_iot_transition.close_body_serial=7;ad->wr_iot_transition.close_body_epoch=9;
 ad->wr_iot_peer_open_owner.serial=11;ad->wr_iot_peer_open_owner.device=ad;ad->wr_iot_peer_open_owner.phase=1;
 wr_iot_mcu_sender_init(&ad->wr_iot_mcu_sender_owner);
 ad->wr_iot_mcu_sender_owner.closed=ad->wr_iot_mcu_sender_owner.release_claimed=ad->wr_iot_mcu_sender_owner.off_done=1;
 ad->wr_iot_mcu_sender_owner.close_serial=7;
 ad->chipOps.pci_kick_out_cmd_msg=AndesMTPciKickOutCmdMsg;
 atomic_context=alloc_fail=sent=refused=transport_result=nest=0;
}
int main(void){
 RTMP_ADAPTER ad;struct wr_iot_mcu_boot_ticket t;
 for(unsigned fault=0;fault<12;fault++){
  init(&ad);
  if(fault==0)ad.wr_iot_peer_open_owner.phase=0;
  if(fault==1)ad.wr_iot_transition.epoch++;
  if(fault==2)ad.wr_iot_transition.close_body_serial=0;
  if(fault==3)ad.wr_iot_mcu_sender_owner.messages=1;
  if(fault==4)ad.wr_iot_mcu_sender_owner.inflight=1;
  if(fault==5)ad.wr_iot_mcu_sender_owner.release_claimed=0;
  if(fault==6)ad.wr_iot_mcu_sender_owner.off_done=0;
  if(fault==7)ad.wr_iot_mcu_sender_owner.uncertain=1;
  if(fault==8)ad.wr_iot_mcu_sender_owner.poisoned=1;
  if(fault==9)ad.MCUCtrl.flags=1;
  if(fault==10)ad.wr_iot_peer_close_executor=1;
  if(fault==11)atomic_context=1;
  assert(wr_iot_mcu_boot_reserve(&ad,11,&t)==1);
 }
 init(&ad);assert(!wr_iot_mcu_boot_reserve(&ad,11,&t));
 assert(wr_iot_mcu_boot_reserve(&ad,11,&t)==1);
 assert(!wr_iot_mcu_boot_alloc(&ad,0,&t)); /* Controller not initialized. */
 ad.MCUCtrl.flags=1;alloc_fail=1;
 assert(!wr_iot_mcu_boot_alloc(&ad,0,&t)&&!ad.wr_iot_mcu_sender_owner.messages);alloc_fail=0;
 assert(!wr_iot_mcu_message_enter(&ad.wr_iot_mcu_sender_owner));
 for(unsigned i=0;i<4;i++){
  struct cmd_msg *m=wr_iot_mcu_boot_alloc(&ad,12,&t);assert(m);
  m->cmd_type=(unsigned[]){1,2,0xef,0xee}[i];m->need_wait=i!=3;
  if(!i)nest=1;
  assert(!wr_iot_mcu_boot_send(&ad,m,&t));
  assert(ad.wr_iot_mcu_sender_owner.closed&&ad.wr_iot_mcu_sender_owner.release_claimed&&!ad.wr_iot_mcu_sender_owner.messages);
 }
 assert(sent==4&&refused==1&&!held);
 for(unsigned fault=0;fault<7;fault++){
  struct cmd_msg *bad=wr_iot_mcu_boot_alloc(&ad,0,&t);assert(bad);
  bad->cmd_type=1;bad->need_wait=1;
  if(fault==0){bad->cmd_type=0xed;bad->ext_cmd_type=5;}
  if(fault==1)bad->need_wait=0;
  if(fault==2)bad->cmd_type=0xee;
  if(fault==3)bad->need_retransmit=1;
  if(fault==4)bad->wr_iot_boot_epoch++;
  if(fault==5)bad->ext_cmd_type=1;
  if(fault==6)ad.chipOps.pci_kick_out_cmd_msg=NULL;
  assert(wr_iot_mcu_boot_send(&ad,bad,&t)==1&&sent==4);
  assert(!ad.wr_iot_mcu_sender_owner.messages&&!ad.wr_iot_mcu_sender_owner.inflight);
  ad.chipOps.pci_kick_out_cmd_msg=AndesMTPciKickOutCmdMsg;
 }

 struct cmd_msg *m=wr_iot_mcu_boot_alloc(&ad,0,&t);assert(m);m->cmd_type=1;m->need_wait=1;
 transport_result=-7;assert(wr_iot_mcu_boot_send(&ad,m,&t)==-7);
 assert(ad.wr_iot_boot_failed&&ad.wr_iot_mcu_sender_owner.uncertain&&!wr_iot_mcu_boot_alloc(&ad,0,&t));
 init(&ad);assert(!wr_iot_mcu_boot_reserve(&ad,11,&t));ad.MCUCtrl.flags=1;t.radio_epoch++;
 assert(!wr_iot_mcu_boot_alloc(&ad,0,&t));
 puts("PASS actual boot reserve/allocator/sender: close/open provenance, exclusive lease, allowed commands, allocation failure, nested send refusal, consumed-message lifetime and failure retention; loader/tasklets/hardware unbound");
}
'''
if 'wr_iot_mcu_boot_freeze(' in (a.candidate/'include/wr-iot-mcu-boot-transport.inc').read_text():
 anchor=' puts("PASS actual boot reserve/allocator/sender:'
 pos=fixture.index(anchor)
 fixture=fixture[:pos]+r'''
 init(&ad);assert(!wr_iot_mcu_boot_reserve(&ad,11,&t));ad.MCUCtrl.flags=1;
 wait_ad=&ad;wait_mode=0;parked=wr_iot_mcu_boot_alloc(&ad,0,&t);assert(parked);
 assert(!wr_iot_mcu_boot_freeze(&ad)&&!parked&&ad.wr_iot_boot_frozen);
 assert(wr_iot_mcu_boot_frozen_owned(&ad)&&!ad.wr_iot_mcu_sender_owner.messages);
 assert(ad.wr_iot_mcu_sender_owner.release_claimed&&!wr_iot_mcu_message_enter(&ad.wr_iot_mcu_sender_owner));
 init(&ad);assert(!wr_iot_mcu_boot_reserve(&ad,11,&t));ad.MCUCtrl.flags=1;
 wait_ad=&ad;wait_mode=1;parked=wr_iot_mcu_boot_alloc(&ad,0,&t);assert(parked);
 assert(wr_iot_mcu_boot_freeze(&ad)==1&&parked&&ad.wr_iot_boot_frozen&&ad.wr_iot_mcu_sender_owner.messages==1);
 AndesForceFreeCmdMsg(parked);parked=NULL;wait_mode=0;
 assert(!wr_iot_mcu_boot_freeze(&ad));
 init(&ad);assert(!wr_iot_mcu_boot_reserve(&ad,11,&t));ad.MCUCtrl.flags=1;
 wait_ad=&ad;wait_mode=2;parked=wr_iot_mcu_boot_alloc(&ad,0,&t);assert(parked);
 assert(wr_iot_mcu_boot_freeze(&ad)==1&&!parked&&ad.wr_iot_boot_frozen);
 assert(!wr_iot_mcu_boot_frozen_owned(&ad));
 init(&ad);assert(!wr_iot_mcu_boot_reserve(&ad,11,&t));ad.wr_iot_mcu_sender_owner.inflight=1;
 assert(wr_iot_mcu_boot_freeze(&ad)==1&&!ad.wr_iot_boot_frozen);
 puts("PASS actual boot construction fence: old private builder drain, late constructor rejection, timeout retention, retry after drain and epoch drift; waits injected");
'''+fixture[pos:]
control=a.candidate/'include/wr-iot-mcu-control-admission.inc'
if control.exists():
 pos=fixture.index('static RTMP_ADAPTER *wait_ad;')
 fixture=fixture[:pos]+control.read_text()+'\n'+fixture[pos:]
 pos=fixture.index(' puts("PASS actual boot reserve/allocator/sender:')
 fixture=fixture[:pos]+r'''
 init(&ad);ad.wr_iot_transition.busy=0;
 assert(wr_iot_control_enter(&ad)&&wr_iot_control_enter(&ad));
 ad.wr_iot_transition.busy=WR_RADIO_START;
 assert(!wr_iot_control_enter(&ad));
 assert(wr_iot_mcu_boot_reserve(&ad,11,&t)==1&&!ad.wr_iot_boot_active);
 wr_iot_control_leave(&ad);assert(ad.wr_iot_control_users==1);
 assert(wr_iot_mcu_boot_reserve(&ad,11,&t)==1);
 wr_iot_control_leave(&ad);assert(!wr_iot_mcu_boot_reserve(&ad,11,&t));
 ad.wr_iot_transition.busy=0;assert(!wr_iot_control_enter(&ad));
 init(&ad);wr_iot_control_leave(&ad);assert(ad.wr_iot_control_poisoned);
 assert(wr_iot_mcu_boot_reserve(&ad,11,&t)==1);
 init(&ad);ad.wr_iot_transition.busy=0;ad.wr_iot_control_users=~0u;
 assert(!wr_iot_control_enter(&ad)&&ad.wr_iot_control_poisoned);
 puts("PASS control admission: producer-first drain, bootstrap-first refusal, nested actors, late release, underflow/overflow retention; locks injected");
'''+fixture[pos:]
with tempfile.TemporaryDirectory(prefix='wr-mcu-boot-transport-') as td:
 c=Path(td)/'check.c';c.write_text(fixture)
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(a.candidate/'include'),'-I'+str(here),str(c),'-o',td+'/check'],check=True)
 subprocess.run([td+'/check'],check=True)
