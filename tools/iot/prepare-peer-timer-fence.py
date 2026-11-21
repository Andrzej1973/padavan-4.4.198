#!/usr/bin/env python3
"""Fence failed insertion timer scheduling/dispatch without freeing or joining."""
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
receipt=json.loads(src.with_name(src.name+'-hardware-insert-consumer.json').read_text())
for name,digest in receipt['output_sha256'].items():
    if hashlib.sha256((src/name).read_bytes()).hexdigest()!=digest:p.error('insertion predecessor mismatch: '+name)
pins={'common/rtmp_init.c':'66f20122bf2b6b7b8d4d3ae1b6777b0ca9d05d5334fe3b30c4aebad87f763456',
      'common/rtmp_timer.c':'40aae7e02a9af4954948c4913c6d0db4e27e48f5373c197fba0d3f5164eea1e3',
      'include/rtmp_timer.h':'5a90cbbc486744aca96d118865136528eefb88d055ead8437f1e0d128d6b4a2e'}
for name,digest in pins.items():
    if hashlib.sha256((src/name).read_bytes()).hexdigest()!=digest:p.error('unreviewed timer implementation: '+name)
changed={}
h=(src/'include/rtmp_timer.h').read_text()
anchor='typedef struct _RALINK_TIMER_STRUCT {'
if h.count(anchor)!=1:p.error('unreviewed timer layout')
h=h.replace(anchor,anchor+'\n\tBOOLEAN wr_iot_retiring; /* Protected by TimerSemLock for scheduling. */',1)
anchor='} RALINK_TIMER_STRUCT, *PRALINK_TIMER_STRUCT;'
if h.count(anchor)!=1:p.error('unreviewed timer typedef')
h=h.replace(anchor,anchor+'\n\nVOID wr_iot_timer_fence(RALINK_TIMER_STRUCT *pTimer);',1)
anchor='\t_pTimer->handle = _func;'
if h.count(anchor)!=1:p.error('unreviewed queued timer macro')
h=h.replace(anchor,'\tif (READ_ONCE(_pTimer->wr_iot_retiring)) return; \\\n'+anchor,1)
anchor='\t_func(NULL, (PVOID) pTimer->cookie, NULL, pTimer);'
if h.count(anchor)!=1:p.error('unreviewed direct timer macro')
h=h.replace(anchor,'\tif (READ_ONCE(pTimer->wr_iot_retiring)) return; \\\n'+anchor,1)
h=h.replace('if (pTimer->Repeat)','if (pTimer->Repeat && !READ_ONCE(pTimer->wr_iot_retiring))',1)
h=h.replace('if ((_pQNode == NULL) && (_pAd->TimerQ.status & RTMP_TASK_CAN_DO_INSERT))',
            'if ((_pQNode == NULL) && !READ_ONCE(_pTimer->wr_iot_retiring) && (_pAd->TimerQ.status & RTMP_TASK_CAN_DO_INSERT))',1)
changed['include/rtmp_timer.h']=h
s=(src/'common/rtmp_init.c').read_text()
for fn in ('RTMPInitTimer','RTMPSetTimer','RTMPModTimer'):
    start=s.index('VOID '+fn+'(');end=s.index('\n}',start)+2;body=s[start:end]
    anchor='\tRTMP_SEM_LOCK(&TimerSemLock);'
    if body.count(anchor)!=1:p.error('unreviewed timer semaphore: '+fn)
    guard='''
\tif (pTimer->Valid && pTimer->wr_iot_retiring) {
\t\tRTMP_SEM_UNLOCK(&TimerSemLock);return;
\t}'''
    body=body.replace(anchor,anchor+guard,1)
    if fn=='RTMPInitTimer':
        body=body.replace('pTimer->Valid      = TRUE;',
                          'pTimer->wr_iot_retiring = FALSE;\n\tpTimer->Valid      = TRUE;',1)
    s=s[:start]+body+s[end:]
fence='''

/* Nonblocking admission fence, not callback synchronization. */
VOID wr_iot_timer_fence(RALINK_TIMER_STRUCT *pTimer)
{
 if (!pTimer) return;
 RTMP_SEM_LOCK(&TimerSemLock);
 if (pTimer->Valid) {
  WRITE_ONCE(pTimer->wr_iot_retiring, TRUE);
  pTimer->Repeat = FALSE;pTimer->State = TRUE;
 }
 RTMP_SEM_UNLOCK(&TimerSemLock);
}
'''
s+=fence;changed['common/rtmp_init.c']=s
s=(src/'common/rtmp_timer.c').read_text()
anchor='if ((pTimer->handle != NULL) && (!pAd->PM_FlgSuspend))'
if s.count(anchor)!=1:p.error('unreviewed timer-task dispatch')
s=s.replace(anchor,anchor[:-1]+' && !READ_ONCE(pTimer->wr_iot_retiring))',1)
anchor='if ((pTimer->Repeat) && (pTimer->State == FALSE))'
if s.count(anchor)!=1:p.error('unreviewed timer-task rearm')
s=s.replace(anchor,anchor[:-1]+' && !READ_ONCE(pTimer->wr_iot_retiring))',1)
changed['common/rtmp_timer.c']=s
s=(src/'include/wr-iot-peer-hardware-insert-result.inc').read_text()
anchor='  if (wr_result != WR_IOT_WCID_APPLIED) {\n   ULONG wr_flags;'
if s.count(anchor)!=1:p.error('unreviewed insertion failure boundary')
s=s.replace(anchor,anchor+'\n#include "wr-iot-peer-failed-timer-fence.inc"',1)
changed['include/wr-iot-peer-hardware-insert-result.inc']=s
shutil.copytree(src,out)
for name,text in changed.items():(out/name).write_text(text,encoding='utf-8',newline='\n')
helper=Path(__file__).with_name('peer-failed-timer-fence.inc')
shutil.copyfile(helper,out/'include/wr-iot-peer-failed-timer-fence.inc')
out.with_name(out.name+'-peer-timer-fence.json').write_text(json.dumps({
 'output_sha256':{n:hashlib.sha256((out/n).read_bytes()).hexdigest() for n in changed},
 'scope':'future schedule/dispatch fence only; admitted callback/rearm race and old reuse still need join',
 'target_compiled':False,'runtime_verified':False,'timer_join_accepted':False,
},indent=2)+'\n')
print('Staged failed-peer timer scheduling/dispatch fence; no release/join')
