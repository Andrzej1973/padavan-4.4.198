#!/usr/bin/env python3
"""Execute actual PCI destructor bodies with generated reservation drop."""
import argparse,subprocess,tempfile
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('candidate',type=Path);a=p.parse_args();here=Path(__file__).resolve().parent
s=(a.candidate/'mcu/andes_core.c').read_text()
start=s.index('VOID AndesFreeCmdMsg(');end=s.index('\nBOOLEAN IsInbandCmdProcessing',start);bodies=s[start:end]
assert bodies.count('unsigned int wr_slot=msg->wr_iot_sequence_slot;')==2
helper=(a.candidate/'include/wr-iot-mcu-message-lifetime.inc').read_text();helper=helper[:helper.index('\nstruct cmd_msg *AndesAllocCmdMsg(')]
code=r'''
#include "mcu-sender-owner.h"
#include "mcu-sequence-reservation.h"
#include <assert.h>
#include <stdlib.h>
#define VOID void
typedef unsigned long ULONG;
typedef void *PNDIS_PACKET;
struct MCU_CTRL {int free_cmd_msg;};
typedef struct {int wr_iot_mcu_sender_lock,wr_iot_mcu_sender_wait;struct MCU_CTRL MCUCtrl;struct wr_iot_mcu_sender_owner wr_iot_mcu_sender_owner;struct wr_iot_mcu_sequence_reservation wr_iot_sequence;} RTMP_ADAPTER;
struct cmd_msg {void *priv;void *net_pkt;int need_wait,ack_done;unsigned int wr_iot_sequence_slot;};
static int held,retired,packets;static RTMP_ADAPTER *target;
static void unlocked(void){assert(target);assert(!target->wr_iot_sequence.occupied);assert(target->MCUCtrl.free_cmd_msg==1);assert(wr_iot_mcu_sender_release_claim(&target->wr_iot_mcu_sender_owner));free(target);target=0;retired++;}
#define RTMP_SPIN_LOCK_IRQSAVE(l,f) do{(void)(l);*(f)=0;assert(!held);held=1;}while(0)
#define RTMP_SPIN_UNLOCK_IRQRESTORE(l,f) do{(void)(l);(void)(f);held=0;unlocked();}while(0)
#define RTMP_OS_EXIT_COMPLETION(p) do{assert(*(p)==7);}while(0)
#define os_free_mem(unused,p) free(p)
static void RTMPFreeNdisPacket(RTMP_ADAPTER *ad,void *p){assert(ad==target&&!held);assert(p);free(p);packets++;}
static void wake_up_all(int *p){(void)p;assert(held);}
'''+helper+bodies+r'''
int main(void){
for(int force=0;force<2;force++)for(int waiting=0;waiting<2;waiting++){
 RTMP_ADAPTER *ad=calloc(1,sizeof(*ad));assert(ad);target=ad;
 wr_iot_mcu_sender_init(&ad->wr_iot_mcu_sender_owner);
 assert(wr_iot_mcu_message_enter(&ad->wr_iot_mcu_sender_owner));
 assert(wr_iot_mcu_sender_close(&ad->wr_iot_mcu_sender_owner,1));
 struct cmd_msg *m=calloc(1,sizeof(*m));assert(m);m->priv=ad;m->need_wait=waiting;m->ack_done=7;
 m->wr_iot_sequence_slot=wr_iot_mcu_sequence_reserve(&ad->wr_iot_sequence);assert(m->wr_iot_sequence_slot);
 if(force){m->net_pkt=malloc(1);assert(m->net_pkt);AndesForceFreeCmdMsg(m);}else AndesFreeCmdMsg(m);
 assert(!target&&!held);
}
assert(retired==4&&packets==2);return 0;}
'''
with tempfile.TemporaryDirectory(prefix='wr-sequence-destructors-') as d:
 c=Path(d)/'check.c';c.write_text(code)
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(c),'-o',d+'/check'],check=True)
 subprocess.run([d+'/check'],check=True)
print('PASS actual PCI free/force-free bodies and generated drop: waiting/nonwaiting, final adapter free; USB/SDIO untested')
