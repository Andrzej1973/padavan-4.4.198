#!/usr/bin/env python3
"""Track the popped/running timer-task callback outside peer memory."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('source',type=Path);p.add_argument('output',type=Path)
a=p.parse_args();src=a.source.resolve(strict=True);out=a.output.resolve()
if out.exists() or src==out or src in out.parents or out in src.parents:
    p.error('new separate output required')
receipt=json.loads(src.with_name(src.name+'-peer-timer-fence.json').read_text())
for name,digest in receipt['output_sha256'].items():
    if hashlib.sha256((src/name).read_bytes()).hexdigest()!=digest:p.error('timer-fence predecessor mismatch: '+name)
changed={}
h=(src/'include/rtmp.h').read_text();anchor='\tNDIS_SPIN_LOCK wr_iot_transition_lock;'
if h.count(anchor)!=1:p.error('unreviewed adapter lifecycle state')
h=h.replace(anchor,'''#ifdef RTMP_TIMER_TASK_SUPPORT
 struct wr_iot_timer_task_owner wr_iot_timer_owner;
 wait_queue_head_t wr_iot_timer_drain_wait;
#endif
'''+anchor,1)
# Must define the owner before the adapter struct, not inside it.
anchor='typedef struct _RTMP_ADAPTER RTMP_ADAPTER;'
if h.count(anchor)!=1:p.error('unreviewed adapter forward declaration')
h=h.replace(anchor,'#include "timer-task-owner.h"\n'+anchor,1)
changed['include/rtmp.h']=h
s=(src/'common/rtmp_init.c').read_text();anchor='\t\tinit_waitqueue_head(&pAd->wr_iot_ticket_wait);'
if s.count(anchor)!=1:p.error('unreviewed adapter publication initialization')
s=s.replace(anchor,anchor+'''
#ifdef RTMP_TIMER_TASK_SUPPORT
        wr_iot_timer_task_owner_init(&pAd->wr_iot_timer_owner);
        init_waitqueue_head(&pAd->wr_iot_timer_drain_wait);
#endif''',1)
changed['common/rtmp_init.c']=s
s=(src/'common/rtmp_timer.c').read_text();start=s.index('static void RtmpTimerQHandle(');end=s.index('\nINT RtmpTimerQThread(',start)
body=s[start:end]
anchor='\tunsigned long\tirqFlag;'
if body.count(anchor)!=1:p.error('unreviewed worker declarations')
body=body.replace(anchor,anchor+'\n\tunsigned long wr_timer_serial;',1)
anchor='\t\t\tRTMP_INT_LOCK(&pAd->TimerQLock, irqFlag);'
if body.count(anchor)!=1:p.error('unreviewed worker pop lock')
body=body.replace(anchor,anchor+'\n\t\t\tpTimer = NULL;wr_timer_serial = 0;',1)
anchor='\t\t\t\tpTimer = pEntry->pRaTimer;'
if body.count(anchor)!=1:p.error('unreviewed worker pop')
body=body.replace(anchor,anchor+'''
                wr_timer_serial = wr_iot_timer_task_owner_begin(&pAd->wr_iot_timer_owner,pTimer);
                if (!wr_timer_serial) pTimer = NULL;''',1)
anchor='\t\t\t\t\tRTMP_OS_Add_Timer(&pTimer->TimerObj, pTimer->TimerValue);'
if body.count(anchor)!=1:p.error('unreviewed last timer access')
body=body.replace(anchor,anchor+'''
                /* Last timer-object access precedes owner release/wakeup. */
                RTMP_INT_LOCK(&pAd->TimerQLock, irqFlag);
                if (wr_iot_timer_task_owner_end(&pAd->wr_iot_timer_owner,pTimer,wr_timer_serial))
                    wake_up_all(&pAd->wr_iot_timer_drain_wait);
                RTMP_INT_UNLOCK(&pAd->TimerQLock, irqFlag);''',1)
s=s[:start]+body+s[end:];changed['common/rtmp_timer.c']=s
shutil.copytree(src,out)
for name,text in changed.items():(out/name).write_text(text,encoding='utf-8',newline='\n')
helper=Path(__file__).with_name('timer-task-owner.h');shutil.copyfile(helper,out/'include/timer-task-owner.h')
out.with_name(out.name+'-timer-task-owner.json').write_text(json.dumps({
 'output_sha256':{n:hashlib.sha256((out/n).read_bytes()).hexdigest() for n in changed},
 'helper_sha256':hashlib.sha256(helper.read_bytes()).hexdigest(),
 'scope':'timer-task execution ownership only; process join/direct timer drain and adapter lifetime unbound',
 'target_compiled':False,'runtime_verified':False,'timer_join_accepted':False,
},indent=2)+'\n')
print('Staged adapter-owned timer-task execution tracking and stale-local reset')
