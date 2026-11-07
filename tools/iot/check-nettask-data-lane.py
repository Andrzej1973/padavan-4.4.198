#!/usr/bin/env python3
"""Execute prepared scheduler and both exits; OS callbacks remain mocked."""
import argparse
from pathlib import Path
import re
import subprocess
import tempfile

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('overlay',type=Path);a=p.parse_args()
net=(a.overlay/'os/linux/rt_rbus_pci_drv.c').read_text()
def body(name):
    start=net.index('INT '+name+'(');return net[start:net.index('\n}',start)+2]
exits=body('RtmpNetTaskExit')+'\n'+body('wr_iot_nettask_data_exit')
fields=sorted(set(re.findall(r'RTMP_OS_TASKLET_KILL\(&pObj->(\w+)\)',exits)))
prefix=r'''
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "nettask-lane-owner.h"
typedef int INT;typedef void VOID;typedef unsigned long ULONG;
typedef struct {int id;} RTMP_NET_TASK_STRUCT;
#define MT_MAC 1
#define RTMP_PCI_SUPPORT 1
#define CONFIG_ANDES_SUPPORT 1
#define CONFIG_AP_SUPPORT 1
#define CONFIG_ATE 1
#define DFS_SUPPORT 1
#define UAPSD_SUPPORT 1
#define HIF_MT 1
#define NDIS_STATUS_SUCCESS 0
#define NDIS_STATUS_FAILURE -1
#define IF_DEV_CONFIG_OPMODE_ON_AP(ad) if(1)
'''
prefix+='struct cookie {'+''.join('RTMP_NET_TASK_STRUCT '+f+';' for f in fields)+'};\ntypedef struct cookie *POS_COOKIE;\n'
prefix+=r'''
typedef struct {
 void *OS_Cookie;struct {int hif_type;} chipCap;int is7603;
 int wr_iot_nettask_lock,wr_iot_nettask_wait;
 unsigned wr_iot_nettask_joined,wr_iot_nettask_initializing,wr_iot_nettask_release_claimed;
 unsigned wr_iot_nettask_data_joined,wr_iot_nettask_data_joining;
 struct wr_iot_tasklet_schedule_owner wr_iot_nettask_owner,wr_iot_nettask_data_owner;
} RTMP_ADAPTER;
#define IS_MT7603(ad) ((ad)->is7603)
static int held,atomic_context,irq_off,scheduled,nested,failed_join,killed[64];
static RTMP_ADAPTER *current;
INT wr_iot_nettask_data_exit(RTMP_ADAPTER *pAd);
static void schedule(RTMP_NET_TASK_STRUCT *task);
#define RTMP_IRQ_LOCK(l,f) do{(void)(l);(f)=0;assert(!held);held=1;}while(0)
#define RTMP_IRQ_UNLOCK(l,f) do{(void)(l);(void)(f);assert(held);held=0;}while(0)
#define RTMP_INT_LOCK RTMP_IRQ_LOCK
#define RTMP_INT_UNLOCK RTMP_IRQ_UNLOCK
#define RTMP_OS_TASKLET_SCHE(t) schedule(t)
#define in_atomic() atomic_context
#define irqs_disabled() irq_off
#define msecs_to_jiffies(n) (n)
#define wait_event_timeout(q,c,t) ((void)(q),assert(!held&&(t)==5000),(c)?1:0)
#define wake_up_all(q) ((void)(q))
'''
prefix+=(a.overlay/'include/wr-iot-nettask-data-drain.inc').read_text()+'\n'
sched=(a.overlay/'include/wr-iot-nettask-schedule.inc').read_text().replace('#include "wr-iot-nettask-data-drain.inc"','')
source=prefix+sched+r'''
static void kill_task(RTMP_NET_TASK_STRUCT *task){
 assert(!held);killed[task->id]++;
 wr_iot_nettask_schedule(current,task); /* Late rearm must be refused. */
}
#define RTMP_OS_TASKLET_KILL(t) kill_task(t)
'''+exits+r'''
static void schedule(RTMP_NET_TASK_STRUCT *task){
 (void)task;assert(!held);scheduled++;
 if(nested){nested=0;failed_join=wr_iot_nettask_data_exit(current);}
}
int main(void){
 RTMP_ADAPTER ad={0};struct cookie cookie={0};current=&ad;
 ad.OS_Cookie=&cookie;ad.is7603=1;ad.chipCap.hif_type=HIF_MT;
 wr_iot_tasklet_schedule_init(&ad.wr_iot_nettask_owner);
 wr_iot_tasklet_schedule_init(&ad.wr_iot_nettask_data_owner);
 ad.wr_iot_nettask_joined=ad.wr_iot_nettask_data_joined=1;
'''
source+='\n'.join('cookie.'+f+'.id='+str(i+1)+';' for i,f in enumerate(fields))
source+=r'''
 assert(wr_iot_nettask_may_initialize(&ad));assert(wr_iot_nettask_open(&ad)==0);
 nested=1;wr_iot_nettask_schedule(&ad,&cookie.rx_done_task);
 assert(failed_join==-1&&!ad.wr_iot_nettask_data_joining);
 assert(!ad.wr_iot_nettask_data_joined&&ad.wr_iot_nettask_data_owner.blocked);
 assert(wr_iot_nettask_data_exit(&ad)==0);
 assert(!killed[cookie.rx1_done_task.id]&&!killed[cookie.hcca_dma_done_task.id]);
 assert(killed[cookie.rx_done_task.id]==1&&ad.wr_iot_nettask_data_joined);
 int old=scheduled;wr_iot_nettask_schedule(&ad,&cookie.rx_done_task);assert(scheduled==old);
 wr_iot_nettask_schedule(&ad,&cookie.rx1_done_task);
 wr_iot_nettask_schedule(&ad,&cookie.hcca_dma_done_task);assert(scheduled==old+2);
 assert(!wr_iot_nettask_may_initialize(&ad));
 ad.wr_iot_nettask_data_joining=1;assert(RtmpNetTaskExit(&ad)==-1);
 ad.wr_iot_nettask_data_joining=0;assert(RtmpNetTaskExit(&ad)==0);
 assert(killed[cookie.rx1_done_task.id]==1&&killed[cookie.hcca_dma_done_task.id]==1);
 old=scheduled;wr_iot_nettask_schedule(&ad,&cookie.rx1_done_task);assert(scheduled==old);
 assert(wr_iot_nettask_may_initialize(&ad));assert(wr_iot_nettask_open(&ad)==0);
 wr_iot_nettask_schedule(&ad,&cookie.rx_done_task);assert(scheduled==old+1);
 ad.is7603=0;assert(wr_iot_nettask_data_exit(&ad)==-1);
 ad.is7603=1;ad.wr_iot_nettask_data_owner.inflight=~0U;
 old=scheduled;wr_iot_nettask_schedule(&ad,&cookie.rx_done_task);
 assert(scheduled==old&&ad.wr_iot_nettask_data_owner.poisoned);
 assert(RtmpNetTaskExit(&ad)==-1&&!ad.wr_iot_nettask_joined);
 assert(!held);
 puts("PASS installed data gate: in-flight schedule refusal, data-only join, MCU continuation, global join/rearm exclusion and initialize fence; mocked OS only");
}
'''
with tempfile.TemporaryDirectory(prefix='wr-data-lane-check-') as temporary:
    root=Path(temporary);(root/'check.c').write_text(source)
    subprocess.run(['gcc','-std=c99','-Wall','-Wextra','-Werror',
                    '-fsanitize=address,undefined','-fno-pie','-no-pie',
                    '-I'+str(a.overlay/'include'),'-I'+str(Path(__file__).resolve().parent),
                    str(root/'check.c'),'-o',str(root/'check')],check=True)
    subprocess.run([str(root/'check')],check=True)
