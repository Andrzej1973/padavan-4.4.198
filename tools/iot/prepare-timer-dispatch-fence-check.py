#!/usr/bin/env python3
"""Extract both real timer macros and worker block; test admission, not joining."""
import argparse
import re
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('candidate',type=Path);p.add_argument('output',type=Path)
a=p.parse_args()
if a.output.exists():p.error('new output required')
h=(a.candidate/'include/rtmp_timer.h').read_text();macros=[]
for match in re.finditer(r'^#define BUILD_TIMER_FUNCTION\(',h,re.M):
    lines=h[match.start():].splitlines(keepends=True);block=''
    for line in lines:
        block+=line
        if not line.rstrip().endswith('\\'):break
    # Windows host pointers are 64-bit, long is 32-bit. Model target-sized data.
    macros.append(block.replace('unsigned long data','uintptr_t data'))
if len(macros)!=2:p.error('unreviewed timer macro count')
s=(a.candidate/'common/rtmp_timer.c').read_text();anchor='\t\t\tif (pTimer)\n\t\t\t{'
if s.count(anchor)!=1:p.error('unreviewed timer-task dispatch block')
start=s.index(anchor);brace=s.index('{',start);depth=0
for end in range(brace,len(s)):
    if s[end]=='{':depth+=1
    elif s[end]=='}':
        depth-=1
        if not depth:break
worker=s[start:end+1]
tracked='wr_iot_timer_task_owner_end' in worker
if tracked:
    assert s.index('wr_iot_timer_task_owner_begin(')<s.index('RTMP_INT_UNLOCK(&pAd->TimerQLock, irqFlag);',s.index('wr_iot_timer_task_owner_begin('))
    assert 'pTimer = NULL;wr_timer_serial = 0;' in s
    assert worker.index('RTMP_OS_Add_Timer')<worker.index('wr_iot_timer_task_owner_end')<worker.index('wake_up_all')
prefix=r'''
#include <assert.h>
#include <stdint.h>
#include <stddef.h>
#define READ_ONCE(v) (v)
#define FALSE 0
#define RTMP_TASK_CAN_DO_INSERT 1
#define OS_HZ 100
typedef void VOID;typedef void *PVOID;
typedef struct {struct {int status;} TimerQ;int PM_FlgSuspend;} RTMP_ADAPTER;
typedef struct timer {int wr_iot_retiring,TimerObj,Repeat,State,TimerValue;uintptr_t cookie;void *pAd;void (*handle)(void*,void*,void*,void*);} RALINK_TIMER_STRUCT,*PRALINK_TIMER_STRUCT;
typedef struct {int dummy;} RTMP_TIMER_TASK_ENTRY;
static int callbacks,arms,inject_callback_fence;
#ifdef RTMP_TIMER_TASK_SUPPORT
static int queue_calls,queue_full,inject_queue_fence;
static RTMP_TIMER_TASK_ENTRY node;
static RTMP_TIMER_TASK_ENTRY *RtmpTimerQInsert(RTMP_ADAPTER *a,RALINK_TIMER_STRUCT *t){
 (void)a;queue_calls++;if(inject_queue_fence)t->wr_iot_retiring=1;return queue_full?NULL:&node;
}
#endif
#define RTMP_OS_Add_Timer(o,v) do{(void)(o);(void)(v);arms++;}while(0)
static void callback(void *a,void *cookie,void *b,void *timer){
 (void)a;(void)b;(void)cookie;callbacks++;
 if(inject_callback_fence)((RALINK_TIMER_STRUCT *)timer)->wr_iot_retiring=1;
}
'''
suffix=r'''
BUILD_TIMER_FUNCTION(callback)
#ifdef RTMP_TIMER_TASK_SUPPORT
static void worker(RALINK_TIMER_STRUCT *pTimer,RTMP_ADAPTER *pAd){
'''+worker+r'''
}
#endif
int main(void){RTMP_ADAPTER a={0};RALINK_TIMER_STRUCT t={0};t.pAd=&a;t.TimerValue=10;t.Repeat=1;
t.wr_iot_retiring=1;rtmp_timer_callback((uintptr_t)&t);assert(!callbacks&&!arms);
#ifdef RTMP_TIMER_TASK_SUPPORT
assert(!queue_calls);a.TimerQ.status=RTMP_TASK_CAN_DO_INSERT;
t.wr_iot_retiring=0;rtmp_timer_callback((uintptr_t)&t);assert(queue_calls==1&&!callbacks&&!arms);
t.wr_iot_retiring=1;worker(&t,&a);assert(!callbacks&&!arms);
t.wr_iot_retiring=0;inject_callback_fence=1;worker(&t,&a);assert(callbacks==1&&!arms);
queue_full=1;inject_queue_fence=1;t.wr_iot_retiring=0;rtmp_timer_callback((uintptr_t)&t);assert(!arms);
inject_queue_fence=0;t.wr_iot_retiring=0;rtmp_timer_callback((uintptr_t)&t);assert(arms==1);
#else
t.wr_iot_retiring=0;inject_callback_fence=1;rtmp_timer_callback((uintptr_t)&t);assert(callbacks==1&&!arms);
t.wr_iot_retiring=0;inject_callback_fence=0;rtmp_timer_callback((uintptr_t)&t);assert(callbacks==2&&arms==1);
#endif
return 0;}
'''
if tracked:
    prefix='#include "timer-task-owner.h"\n'+prefix
    prefix=prefix.replace('int PM_FlgSuspend;} RTMP_ADAPTER;',
        'int PM_FlgSuspend,TimerQLock,wr_iot_timer_drain_wait;struct wr_iot_timer_task_owner wr_iot_timer_owner;} RTMP_ADAPTER;')
    prefix+='''
#ifdef RTMP_TIMER_TASK_SUPPORT
static int owner_lock;
#define RTMP_INT_LOCK(l,f) do{(void)(l);(f)=0;assert(!owner_lock);owner_lock=1;}while(0)
#define RTMP_INT_UNLOCK(l,f) do{(void)(l);(void)(f);assert(owner_lock);owner_lock=0;}while(0)
#define wake_up_all(w) do{(void)(w);assert(owner_lock);}while(0)
#endif
'''
    prefix=prefix.replace('(void)a;(void)b;(void)cookie;callbacks++;', '''(void)a;(void)b;(void)cookie;callbacks++;
#ifdef RTMP_TIMER_TASK_SUPPORT
assert(!wr_iot_timer_task_owner_idle_for(&((RTMP_ADAPTER *)((RALINK_TIMER_STRUCT *)timer)->pAd)->wr_iot_timer_owner,timer));
#endif''')
    suffix=suffix.replace('static void worker(RALINK_TIMER_STRUCT *pTimer,RTMP_ADAPTER *pAd){', '''static void worker(RALINK_TIMER_STRUCT *pTimer,RTMP_ADAPTER *pAd){
unsigned long irqFlag,wr_timer_serial;
RTMP_INT_LOCK(&pAd->TimerQLock,irqFlag);
wr_timer_serial=wr_iot_timer_task_owner_begin(&pAd->wr_iot_timer_owner,pTimer);
if(!wr_timer_serial)pTimer=NULL;
RTMP_INT_UNLOCK(&pAd->TimerQLock,irqFlag);''')
a.output.write_text(prefix+'\n#ifdef RTMP_TIMER_TASK_SUPPORT\n'+macros[0]+'\n#else\n'+macros[1]+'\n#endif\n'+suffix,encoding='utf-8')
print('Extracted direct/task timer dispatch; host pointer-width adaptation, no concurrency join claim')
