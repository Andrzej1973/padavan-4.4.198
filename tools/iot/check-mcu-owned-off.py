#!/usr/bin/env python3
"""Run actual owned-OFF code with mocked OS/transport; not target/ACK proof."""
import argparse
from pathlib import Path
import subprocess
import tempfile

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--candidate', type=Path)
a = p.parse_args(); here = Path(__file__).resolve().parent
includes = a.candidate / 'include' if a.candidate else here
owned = includes / ('wr-iot-mcu-owned-off.inc' if a.candidate else 'mcu-owned-off.inc')
drain = includes / ('wr-iot-mcu-sender-drain.inc' if a.candidate else 'mcu-sender-drain.inc')
source = r'''
#include <assert.h>
#include <stdlib.h>
#include <stdio.h>
#include "mcu-sender-owner.h"
#include "radio-transition.h"
typedef unsigned long ULONG;
typedef int INT;
typedef int INT32;
#define TRUE 1
#define NDIS_STATUS_SUCCESS 0
#define NDIS_STATUS_FAILURE -1
#define EXT_CID 0xed
#define EXT_CMD_RADIO_ON_OFF_CTRL 5
typedef struct {
 int wr_iot_transition_lock,wr_iot_mcu_sender_lock,wr_iot_mcu_sender_wait;
 struct {unsigned long serial,epoch;unsigned busy,mt_radio_off_stage;} wr_iot_transition;
 struct wr_iot_mcu_sender_owner wr_iot_mcu_sender_owner;
} RTMP_ADAPTER;
struct cmd_msg {int need_wait,need_retransmit,need_rsp,cmd_type,ext_cmd_type,wr_iot_checked;};
static int transition_held,sender_held,atomic_context,irq_off,finish_wait,invalidate_wait;
static int sent,freed,wakes,transport_result;
#define in_atomic() atomic_context
#define irqs_disabled() irq_off
#define RTMP_IRQ_LOCK(l,f) do{(void)(l);(f)=0;assert(!transition_held&&!sender_held);transition_held=1;}while(0)
#define RTMP_IRQ_UNLOCK(l,f) do{(void)(l);(void)(f);assert(transition_held&&!sender_held);transition_held=0;}while(0)
#define RTMP_SPIN_LOCK_IRQSAVE(l,f) do{(void)(l);*(f)=0;assert(!sender_held);sender_held=1;}while(0)
#define RTMP_SPIN_UNLOCK_IRQRESTORE(l,f) do{(void)(l);(void)(f);assert(sender_held);sender_held=0;}while(0)
#define msecs_to_jiffies(n) (n)
static void before_wait(RTMP_ADAPTER *ad){
 assert(!transition_held&&!sender_held);
 if(finish_wait)assert(wr_iot_mcu_sender_leave(&ad->wr_iot_mcu_sender_owner));
 if(invalidate_wait)ad->wr_iot_transition.epoch++;
}
#define wait_event_timeout(q,c,t) ((void)(q),assert((t)==5000),before_wait(ad),(c)?1:0)
static void wake_up_all(int *q){(void)q;assert(sender_held);wakes++;}
static void AndesForceFreeCmdMsg(struct cmd_msg *msg){
 assert(!transition_held&&!sender_held);freed++;free(msg);
}
static int wr_iot_mcu_send_body(RTMP_ADAPTER *ad,struct cmd_msg *msg){
 struct wr_iot_mcu_sender_owner *s=&ad->wr_iot_mcu_sender_owner;
 assert(!transition_held&&!sender_held&&s->closed&&s->off_active&&!s->inflight);
 assert(msg->wr_iot_checked&&!msg->need_retransmit);
 assert(!wr_iot_mcu_sender_enter(s)&&!wr_iot_mcu_sender_release_claim(s));
 sent++;free(msg);return transport_result;
}
'''
source += drain.read_text() + '\n' + owned.read_text() + r'''
static struct cmd_msg *message(void){
 struct cmd_msg *m=calloc(1,sizeof(*m));assert(m);
 m->need_wait=m->need_rsp=1;m->cmd_type=EXT_CID;m->ext_cmd_type=5;return m;
}
static void init(RTMP_ADAPTER *ad){
 *ad=(RTMP_ADAPTER){0};wr_iot_mcu_sender_init(&ad->wr_iot_mcu_sender_owner);
 ad->wr_iot_transition.serial=7;ad->wr_iot_transition.epoch=3;
 ad->wr_iot_transition.busy=WR_RADIO_CLOSE;ad->wr_iot_transition.mt_radio_off_stage=2;
 finish_wait=invalidate_wait=atomic_context=irq_off=0;transport_result=0;
}
int main(void){
 RTMP_ADAPTER ad;struct wr_iot_radio_ticket t={.serial=7,.epoch=3,.operation=WR_RADIO_CLOSE};
 init(&ad);assert(wr_iot_mcu_sender_enter(&ad.wr_iot_mcu_sender_owner));finish_wait=1;
 assert(wr_iot_mcu_send_owned_off(&ad,message(),&t)==0);
 assert(sent==1&&wakes==1&&ad.wr_iot_mcu_sender_owner.off_done);
 finish_wait=0;assert(wr_iot_mcu_send_owned_off(&ad,message(),&t)==-1&&sent==1);
 assert(!wr_iot_mcu_sender_enter(&ad.wr_iot_mcu_sender_owner));
 init(&ad);transport_result=-9;
 assert(wr_iot_mcu_send_owned_off(&ad,message(),&t)==-9);
 assert(ad.wr_iot_mcu_sender_owner.closed&&ad.wr_iot_mcu_sender_owner.uncertain);
 assert(!wr_iot_mcu_sender_release_claim(&ad.wr_iot_mcu_sender_owner));
 assert(wr_iot_mcu_send_owned_off(&ad,message(),&t)==-1&&sent==2);
 init(&ad);assert(wr_iot_mcu_sender_enter(&ad.wr_iot_mcu_sender_owner));
 assert(wr_iot_mcu_send_owned_off(&ad,message(),&t)==-1&&sent==2);
 assert(ad.wr_iot_mcu_sender_owner.inflight==1&&ad.wr_iot_mcu_sender_owner.closed);
 assert(wr_iot_mcu_sender_leave(&ad.wr_iot_mcu_sender_owner));
 init(&ad);invalidate_wait=1;
 assert(wr_iot_mcu_send_owned_off(&ad,message(),&t)==-1&&sent==2);
 assert(!ad.wr_iot_mcu_sender_owner.off_active&&ad.wr_iot_mcu_sender_owner.closed);
 init(&ad);t.serial=8;
 assert(wr_iot_mcu_send_owned_off(&ad,message(),&t)==-1&&!ad.wr_iot_mcu_sender_owner.closed);
 t.serial=7;atomic_context=1;
 assert(wr_iot_mcu_send_owned_off(&ad,message(),&t)==-1&&!ad.wr_iot_mcu_sender_owner.closed);
 atomic_context=0;irq_off=1;
 assert(wr_iot_mcu_send_owned_off(&ad,message(),&t)==-1&&!ad.wr_iot_mcu_sender_owner.closed);
 irq_off=0;struct cmd_msg *m=message();m->need_retransmit=1;
 assert(wr_iot_mcu_send_owned_off(&ad,m,&t)==-1&&!ad.wr_iot_mcu_sender_owner.closed);
 assert(!transition_held&&!sender_held&&freed==8);
 puts("PASS owned OFF: drain, ticket revalidation, exclusive lease, no replay, failure retention and consumed-message lifetime; mocked transport only");
}
'''
with tempfile.TemporaryDirectory(prefix='wr-owned-off-') as temporary:
    root = Path(temporary); (root/'check.c').write_text(source)
    subprocess.run(['gcc','-std=c99','-Wall','-Wextra','-Werror',
                    '-fsanitize=address,undefined','-fno-pie','-no-pie',
                    '-I'+str(includes),str(root/'check.c'),'-o',str(root/'check')],check=True)
    subprocess.run([str(root/'check')],check=True)
