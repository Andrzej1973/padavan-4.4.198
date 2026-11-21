#!/usr/bin/env python3
"""Run actual submission helper and network Init/Exit with kernel calls mocked."""
import argparse,re
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('candidate',type=Path);p.add_argument('output',type=Path)
a=p.parse_args()
if a.output.exists():p.error('new fixture output required')
s=(a.candidate/'os/linux/rt_rbus_pci_drv.c').read_text()
def function(sig):
 start=s.index(sig);return s[start:s.index('\n}',start)+2]
init=function('NDIS_STATUS RtmpNetTaskInit(');exit=function('INT RtmpNetTaskExit(')
names=sorted(set(re.findall(r'&pObj->(\w+)',init+exit)))
assert 'wr_iot_nettask_block_drain' in exit
assert exit.index('wr_iot_nettask_block_drain')<exit.index('RTMP_OS_TASKLET_KILL')
prefix=r'''
#include "tasklet-schedule-owner.h"
#include <assert.h>
#include <string.h>
typedef void VOID;typedef int INT;typedef int NDIS_STATUS;typedef unsigned long ULONG;
typedef struct {int initialized,killed;} RTMP_NET_TASK_STRUCT;
typedef struct cookie { COOKIE_FIELDS } COOKIE,*POS_COOKIE;
typedef struct {void *OS_Cookie;int wr_iot_nettask_lock,wr_iot_nettask_wait;
 struct wr_iot_tasklet_schedule_owner wr_iot_nettask_owner;unsigned int wr_iot_nettask_joined;} RTMP_ADAPTER;
#define NDIS_STATUS_SUCCESS 0
#define NDIS_STATUS_FAILURE 1
static int held,atomic_context,disabled_irqs,scheduled,kills,initializations,block_during_submit,drain_on_wait;
static RTMP_ADAPTER *current;
#define RTMP_IRQ_LOCK(l,f) do{(void)(l);(f)=0;assert(!held);held=1;}while(0)
#define RTMP_IRQ_UNLOCK(l,f) do{(void)(l);(void)(f);assert(held);held=0;}while(0)
#define wake_up_all(q) do{(void)(q);assert(!held);}while(0)
#define in_atomic() (atomic_context)
#define irqs_disabled() (disabled_irqs)
#define msecs_to_jiffies(ms) (ms)
static int fake_wait(void){assert(!held);if(drain_on_wait){assert(current->wr_iot_nettask_owner.inflight==1);
 current->wr_iot_nettask_owner.inflight=0;drain_on_wait=0;}return 1;}
#define wait_event_timeout(q,condition,timeout) ((void)(q),(void)(timeout),fake_wait(),(condition)?1:0)
static void fake_schedule(RTMP_NET_TASK_STRUCT *task){
 assert(!held&&task->initialized&&!task->killed);scheduled++;
 if(block_during_submit){block_during_submit=0;wr_iot_tasklet_schedule_block(&current->wr_iot_nettask_owner);}
}
#define RTMP_OS_TASKLET_SCHE(task) fake_schedule(task)
/* Callback/data ABI not executed by this host fixture (Windows LLP64). */
#define RTMP_OS_TASKLET_INIT(ad,task,func,data) do{(void)(ad);assert(!held);(task)->initialized=1;(task)->killed=0;initializations++;}while(0)
#define RTMP_OS_TASKLET_KILL(task) do{assert(!held&&!(current->wr_iot_nettask_owner.inflight));assert(current->wr_iot_nettask_owner.blocked);assert(!(task)->killed);(task)->killed=1;kills++;}while(0)
#define IF_DEV_CONFIG_OPMODE_ON_AP(ad) if((void)(ad),1)
#include "wr-iot-nettask-schedule.inc"
'''
prefix=prefix.replace('COOKIE_FIELDS',';'.join('RTMP_NET_TASK_STRUCT '+n for n in names)+';')
post=r'''
int main(void){COOKIE cookie={0};RTMP_ADAPTER a={0};int before;
 a.OS_Cookie=&cookie;current=&a;wr_iot_tasklet_schedule_init(&a.wr_iot_nettask_owner);a.wr_iot_nettask_joined=1;
 assert(RtmpNetTaskInit(&a)==0&&initializations>0&&!a.wr_iot_nettask_joined);
 before=initializations;assert(RtmpNetTaskInit(&a)==1&&initializations==before);
 block_during_submit=1;wr_iot_nettask_schedule(&a,&cookie.rx_done_task);
 assert(scheduled==1&&a.wr_iot_nettask_owner.blocked&&!a.wr_iot_nettask_owner.inflight);
 wr_iot_nettask_schedule(&a,&cookie.rx_done_task);assert(scheduled==1);
 a.wr_iot_nettask_owner.inflight=1;assert(RtmpNetTaskExit(&a)==1&&!kills&&!a.wr_iot_nettask_joined);
 drain_on_wait=1;assert(RtmpNetTaskExit(&a)==0&&kills==initializations&&a.wr_iot_nettask_joined);
 before=kills;assert(RtmpNetTaskExit(&a)==0&&kills==before);
 wr_iot_nettask_schedule(&a,&cookie.rx_done_task);assert(scheduled==1);
 assert(RtmpNetTaskInit(&a)==0&&!a.wr_iot_nettask_joined);
 wr_iot_nettask_schedule(&a,&cookie.rx_done_task);assert(scheduled==2);
 atomic_context=1;assert(RtmpNetTaskExit(&a)==1&&kills==before&&a.wr_iot_nettask_owner.blocked);
 atomic_context=0;disabled_irqs=1;assert(RtmpNetTaskExit(&a)==1&&kills==before);
 disabled_irqs=0;assert(RtmpNetTaskExit(&a)==0&&kills==initializations);
 assert(!held);return 0;}
'''
if 'wr_iot_nettask_release_claimed' in (a.candidate/'include/wr-iot-nettask-schedule.inc').read_text():
 prefix=prefix.replace('unsigned int wr_iot_nettask_joined;',
  'unsigned int wr_iot_nettask_joined;unsigned int wr_iot_nettask_release_claimed,wr_iot_nettask_initializing;')
 post=post.replace(' assert(!held);return 0;}', '''
 before=initializations;
 assert(wr_iot_nettask_may_initialize(&a));
 assert(a.wr_iot_nettask_initializing);
 assert(!wr_iot_nettask_may_initialize(&a));
 assert(wr_iot_nettask_block_drain(&a)==1&&initializations==before);
 assert(a.wr_iot_nettask_joined);
 a.wr_iot_nettask_initializing=0; /* End simulated reservation; no task storage allocated. */
 a.wr_iot_nettask_release_claimed=1;before=initializations;
 assert(RtmpNetTaskInit(&a)==1&&initializations==before);
 assert(wr_iot_nettask_open(&a)==1&&a.wr_iot_nettask_joined);
 wr_iot_nettask_schedule(&a,&cookie.rx_done_task);assert(scheduled==2);
 assert(!held);return 0;}''')
a.output.write_text(prefix+init+exit+post,encoding='utf-8')
print('Extracted scheduling helper and actual network Init/Exit; kernel allocation/scheduler/waits mocked')
