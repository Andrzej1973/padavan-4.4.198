#!/usr/bin/env python3
"""Execute actual AP release admission; join/IRQ receipts and destructors mocked."""
from pathlib import Path
import argparse
import subprocess
import tempfile

here=Path(__file__).resolve().parent
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--candidate',type=Path);args=p.parse_args()
fragment=(here/'ap-release-after-join.inc').read_text()
if args.candidate:
    source=(args.candidate/'ap/ap.c').read_text()
    start=source.index('BOOLEAN wr_iot_ap_release_after_join(')
    fragment=source[start:source.index('\n}',start)+2]
prefix=r'''
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "radio-transition.h"
#include "tasklet-schedule-owner.h"
#include "mcu-sender-owner.h"
typedef int BOOLEAN;typedef unsigned long ULONG;
#define TRUE 1
#define FALSE 0
#define fRTMP_ADAPTER_INTERRUPT_IN_USE 1
typedef struct {
 int wr_iot_transition_lock,wr_iot_nettask_lock,wr_iot_mcu_sender_lock;
 struct {unsigned long serial,epoch,ap_cleanup_serial;unsigned busy,mt_radio_off_stage,shutdown_stage;} wr_iot_transition;
 unsigned wr_iot_nettask_joined,wr_iot_nettask_data_joined,wr_iot_nettask_data_joining,flags;
 unsigned wr_iot_nettask_initializing,wr_iot_nettask_release_claimed;
 struct wr_iot_tasklet_schedule_owner wr_iot_nettask_owner,wr_iot_nettask_data_owner;
 struct wr_iot_mcu_sender_owner wr_iot_mcu_sender_owner;
} RTMP_ADAPTER;
static RTMP_ADAPTER *current;
static int transition_held,net_held,sender_held,atomic_context,irq_off,releases,cleanups,race_init;
#define in_atomic() atomic_context
#define irqs_disabled() irq_off
#define RTMP_TEST_FLAG(ad,flag) ((ad)->flags&(flag))
static void lock_irq(int *lock){
 if(lock==&current->wr_iot_transition_lock){assert(!transition_held&&!net_held&&!sender_held);transition_held=1;}
 else{assert(lock==&current->wr_iot_nettask_lock&&!net_held&&!sender_held);net_held=1;}
}
static void unlock_irq(int *lock){
 if(lock==&current->wr_iot_nettask_lock){assert(net_held&&!sender_held);net_held=0;}
 else{assert(lock==&current->wr_iot_transition_lock&&transition_held&&!net_held&&!sender_held);transition_held=0;}
}
#define RTMP_IRQ_LOCK(l,f) do{(f)=0;lock_irq(l);}while(0)
#define RTMP_IRQ_UNLOCK(l,f) do{(void)(f);unlock_irq(l);}while(0)
#define RTMP_INT_LOCK RTMP_IRQ_LOCK
#define RTMP_INT_UNLOCK RTMP_IRQ_UNLOCK
#define RTMP_SPIN_LOCK_IRQSAVE(l,f) do{(void)(l);*(f)=0;assert(transition_held&&!net_held&&!sender_held);sender_held=1;}while(0)
#define RTMP_SPIN_UNLOCK_IRQRESTORE(l,f) do{(void)(l);(void)(f);assert(transition_held&&sender_held);sender_held=0;if(race_init){current->wr_iot_nettask_initializing=1;race_init=0;}}while(0)
#define IF_DEV_CONFIG_OPMODE_ON_AP(ad) if((ad)!=0)
#define MeasureReqTabExit(ad) ((void)(ad),cleanups++)
#define TpcReqTabExit(ad) ((void)(ad),cleanups++)
#define AutoChBssTableDestroy(ad) ((void)(ad),cleanups++)
#define ChannelInfoDestroy(ad) ((void)(ad),cleanups++)
static void wr_iot_ap_release_resource_body(RTMP_ADAPTER *ad){
 assert(ad&&!transition_held&&!net_held&&!sender_held);releases++;
}
'''
suffix=r'''
static void init(RTMP_ADAPTER *ad){
 memset(ad,0,sizeof(*ad));current=ad;atomic_context=irq_off=race_init=0;
 ad->wr_iot_transition.serial=7;ad->wr_iot_transition.epoch=3;
 ad->wr_iot_transition.busy=WR_RADIO_CLOSE;ad->wr_iot_transition.mt_radio_off_stage=4;
 ad->wr_iot_transition.shutdown_stage=6;
 wr_iot_tasklet_schedule_init(&ad->wr_iot_nettask_owner);
 wr_iot_tasklet_schedule_init(&ad->wr_iot_nettask_data_owner);
 ad->wr_iot_nettask_joined=ad->wr_iot_nettask_data_joined=1;
 wr_iot_mcu_sender_init(&ad->wr_iot_mcu_sender_owner);
 assert(wr_iot_mcu_sender_close(&ad->wr_iot_mcu_sender_owner,7));
 assert(wr_iot_mcu_sender_off_begin(&ad->wr_iot_mcu_sender_owner,7));
 assert(wr_iot_mcu_sender_off_finish(&ad->wr_iot_mcu_sender_owner,7,1));
}
int main(void){
 RTMP_ADAPTER ad;struct wr_iot_radio_ticket t={.serial=7,.epoch=3,.operation=WR_RADIO_CLOSE};
 init(&ad);assert(wr_iot_ap_release_after_join(&ad,&t));
 assert(releases==1&&cleanups==4&&ad.wr_iot_transition.ap_cleanup_serial==7);
 assert(ad.wr_iot_nettask_release_claimed&&ad.wr_iot_mcu_sender_owner.release_claimed);
 assert(!wr_iot_mcu_message_enter(&ad.wr_iot_mcu_sender_owner));
 assert(wr_iot_ap_release_after_join(&ad,&t)&&releases==1&&cleanups==4);
 init(&ad);ad.wr_iot_nettask_joined=0;assert(!wr_iot_ap_release_after_join(&ad,&t));
 init(&ad);ad.wr_iot_nettask_data_joining=1;assert(!wr_iot_ap_release_after_join(&ad,&t));
 init(&ad);ad.wr_iot_mcu_sender_owner.messages=1;assert(!wr_iot_ap_release_after_join(&ad,&t));
 init(&ad);ad.wr_iot_mcu_sender_owner.uncertain=1;assert(!wr_iot_ap_release_after_join(&ad,&t));
 init(&ad);ad.flags=fRTMP_ADAPTER_INTERRUPT_IN_USE;assert(!wr_iot_ap_release_after_join(&ad,&t));
 assert(!ad.wr_iot_mcu_sender_owner.release_claimed&&!ad.wr_iot_nettask_release_claimed);
 init(&ad);ad.wr_iot_transition.epoch++;assert(!wr_iot_ap_release_after_join(&ad,&t));
 init(&ad);ad.wr_iot_transition.shutdown_stage=4;assert(!wr_iot_ap_release_after_join(&ad,&t));
 init(&ad);atomic_context=1;assert(!wr_iot_ap_release_after_join(&ad,&t));
 init(&ad);race_init=1;assert(!wr_iot_ap_release_after_join(&ad,&t));
 assert(ad.wr_iot_mcu_sender_owner.release_claimed&&!ad.wr_iot_nettask_release_claimed);
 assert(releases==1&&cleanups==4&&!transition_held&&!net_held&&!sender_held);
 puts("PASS AP release admission: full join, OFF/message drain, released IRQ, epoch/serial and one-time cleanup; mocked receipts only");
}
'''
with tempfile.TemporaryDirectory(prefix='wr-ap-release-') as temporary:
    root=Path(temporary);(root/'check.c').write_text(prefix+fragment+suffix)
    includes=['-I'+str(here)]
    if args.candidate:includes.insert(0,'-I'+str(args.candidate/'include'))
    subprocess.run(['gcc','-std=c99','-Wall','-Wextra','-Werror','-fsanitize=address,undefined',
                    '-fno-pie','-no-pie',*includes,str(root/'check.c'),'-o',str(root/'check')],check=True)
    subprocess.run([str(root/'check')],check=True)
