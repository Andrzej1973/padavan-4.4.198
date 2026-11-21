#!/usr/bin/env python3
"""Execute actual PCI destructor bodies with generated reservation drop."""
import argparse,subprocess,tempfile
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('candidate',type=Path);a=p.parse_args();here=Path(__file__).resolve().parent
s=(a.candidate/'mcu/andes_core.c').read_text()
start=s.index('VOID AndesFreeCmdMsg(');end=s.index('\nBOOLEAN IsInbandCmdProcessing',start);bodies=s[start:end]
assert bodies.count('unsigned int wr_slot=msg->wr_iot_sequence_slot;')==2
assert bodies.count('unsigned int wr_uncertain=msg->wr_iot_sequence_uncertain;')==2
assert s.count('msg->wr_iot_sequence_uncertain=1;')==1
assert 'msg->wr_iot_sequence_uncertain=0;' not in s
helper=(a.candidate/'include/wr-iot-mcu-message-lifetime.inc').read_text();helper=helper[:helper.index('\nstruct cmd_msg *AndesAllocCmdMsg(')]
release=(a.candidate/'include/wr-iot-mcu-sender-release.inc').read_text()
code=r'''
#include "mcu-sender-owner.h"
#include "mcu-sequence-reservation.h"
#include <assert.h>
#include <stdlib.h>
#define VOID void
typedef int INT;
#define NDIS_STATUS_FAILURE -1
#define NDIS_STATUS_SUCCESS 0
typedef unsigned long ULONG;
typedef void *PNDIS_PACKET;
struct MCU_CTRL {int free_cmd_msg;};
typedef struct {int wr_iot_mcu_sender_lock,wr_iot_mcu_sender_wait;struct MCU_CTRL MCUCtrl;struct wr_iot_mcu_sender_owner wr_iot_mcu_sender_owner;struct wr_iot_mcu_sequence_reservation wr_iot_sequence;} RTMP_ADAPTER;
struct cmd_msg {void *priv;void *net_pkt;int need_wait,ack_done;unsigned int wr_iot_sequence_slot,wr_iot_sequence_uncertain;};
static int held,retired,packets,uncertain_case,finalize_hook=1;static RTMP_ADAPTER *target;
static void unlocked(void);
#define RTMP_SPIN_LOCK_IRQSAVE(l,f) do{(void)(l);*(f)=0;assert(!held);held=1;}while(0)
#define RTMP_SPIN_UNLOCK_IRQRESTORE(l,f) do{(void)(l);(void)(f);held=0;if(finalize_hook)unlocked();}while(0)
#define RTMP_OS_EXIT_COMPLETION(p) do{assert(*(p)==7);}while(0)
#define os_free_mem(unused,p) free(p)
static void RTMPFreeNdisPacket(RTMP_ADAPTER *ad,void *p){assert(ad==target&&!held);assert(p);free(p);packets++;}
static void wake_up_all(int *p){(void)p;assert(held);}
'''+helper+bodies+release+r'''
static void unlocked(void){
 assert(target&&!target->wr_iot_sequence.occupied&&target->MCUCtrl.free_cmd_msg==1);
 finalize_hook=0;
 int result=wr_iot_mcu_sender_release_begin(target);
 finalize_hook=1;
 if(uncertain_case){
  assert(result==NDIS_STATUS_FAILURE&&target->wr_iot_sequence.quarantined);
  assert(!target->wr_iot_mcu_sender_owner.release_claimed);return;
 }
 assert(result==NDIS_STATUS_SUCCESS);free(target);target=0;retired++;
}
int main(void){
for(int force=0;force<2;force++)for(int waiting=0;waiting<2;waiting++)for(int uncertain=0;uncertain<2;uncertain++){
 uncertain_case=uncertain;
 RTMP_ADAPTER *ad=calloc(1,sizeof(*ad));assert(ad);target=ad;
 wr_iot_mcu_sender_init(&ad->wr_iot_mcu_sender_owner);
 assert(wr_iot_mcu_message_enter(&ad->wr_iot_mcu_sender_owner));
 assert(wr_iot_mcu_sender_close(&ad->wr_iot_mcu_sender_owner,1));
 struct cmd_msg *m=calloc(1,sizeof(*m));assert(m);m->priv=ad;m->need_wait=waiting;m->ack_done=7;
 m->wr_iot_sequence_slot=wr_iot_mcu_sequence_reserve(&ad->wr_iot_sequence);assert(m->wr_iot_sequence_slot);
 m->wr_iot_sequence_uncertain=uncertain;
 if(force){m->net_pkt=malloc(1);assert(m->net_pkt);AndesForceFreeCmdMsg(m);}else AndesFreeCmdMsg(m);
 if(uncertain){
  assert(target==ad&&ad->wr_iot_sequence.quarantined&&!held);
  /* Dispose the private test allocation, not a production release receipt. */
  free(target);target=0;
 }
 assert(!target&&!held);
}
assert(retired==4&&packets==4);return 0;}
'''
with tempfile.TemporaryDirectory(prefix='wr-sequence-destructors-') as d:
 c=Path(d)/'check.c';c.write_text(code)
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(c),'-o',d+'/check'],check=True)
 subprocess.run([d+'/check'],check=True)
print('PASS actual PCI destructors/drop/release: normal final free, timeout quarantine refuses release; USB/SDIO untested')
