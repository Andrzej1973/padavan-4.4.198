#!/usr/bin/env python3
"""Add explicit process-context timer join API; do not bind peer freeing yet."""
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
receipt=json.loads(src.with_name(src.name+'-timer-task-owner.json').read_text())
for name,digest in receipt['output_sha256'].items():
    if hashlib.sha256((src/name).read_bytes()).hexdigest()!=digest:p.error('timer-owner predecessor mismatch: '+name)
pins={'os/linux/rt_linux.c':'675d9800e462a161d28cc07bc36356a8f6a34ab5f051d8987245fa2b33bb2974',
      'include/rt_os_util.h':'5eedd352b0c8606ee71aee5aabce69c514514724023c84c3ca46a8fee1db459a',
      'os/linux/rt_linux_symb.c':'0bb398d86e6730254e203619597c5b3ca543819b2a673665cd211c7f8ad638de'}
for name,digest in pins.items():
    if hashlib.sha256((src/name).read_bytes()).hexdigest()!=digest:p.error('unreviewed Linux utility input: '+name)
changed={}
s=(src/'os/linux/rt_linux.c').read_text();s+='\n#include "wr-iot-timer-os-join.inc"\n';changed['os/linux/rt_linux.c']=s
s=(src/'common/rtmp_timer.c').read_text();s+='\n#include "wr-iot-timer-checked-join.inc"\n';changed['common/rtmp_timer.c']=s
s=(src/'include/rt_os_util.h').read_text();anchor='VOID RTMP_OS_Del_Timer(NDIS_MINIPORT_TIMER *pTimerOrg, BOOLEAN *pCancelled);'
if s.count(anchor)!=1:p.error('unreviewed OS timer prototype')
s=s.replace(anchor,anchor+'''
INT wr_iot_os_join_context(VOID);
INT wr_iot_os_sync_timer(NDIS_MINIPORT_TIMER *timer);
INT wr_iot_os_timer_task_current(RTMP_OS_TASK *task);''',1);changed['include/rt_os_util.h']=s
s=(src/'include/rtmp.h').read_text();anchor='VOID RTMPSetTimer('
# Match full prototype through semicolon despite multiline arguments.
start=s.index(anchor);end=s.index(';',start)+1
s=s[:end]+'''
/* Process context, exclusive adapter/timer ownership, no MAC/IRQ locks. */
BOOLEAN wr_iot_timer_join_checked(RTMP_ADAPTER *pAd,RALINK_TIMER_STRUCT *timer,ULONG timeout_ms);
'''+s[end:];changed['include/rtmp.h']=s
s=(src/'os/linux/rt_linux_symb.c').read_text();anchor='EXPORT_SYMBOL(RTMP_OS_Del_Timer);'
if s.count(anchor)!=1:p.error('unreviewed utility export')
s=s.replace(anchor,anchor+'''
EXPORT_SYMBOL(wr_iot_os_join_context);
EXPORT_SYMBOL(wr_iot_os_sync_timer);
EXPORT_SYMBOL(wr_iot_os_timer_task_current);''',1);changed['os/linux/rt_linux_symb.c']=s
shutil.copytree(src,out)
for name,text in changed.items():(out/name).write_text(text,encoding='utf-8',newline='\n')
for local,target in [('timer-os-join.inc','wr-iot-timer-os-join.inc'),('timer-checked-join.inc','wr-iot-timer-checked-join.inc')]:
    shutil.copyfile(Path(__file__).with_name(local),out/'include'/target)
out.with_name(out.name+'-timer-checked-join.json').write_text(json.dumps({
 'output_sha256':{n:hashlib.sha256((out/n).read_bytes()).hexdigest() for n in changed},
 'helper_sha256':{n:hashlib.sha256((out/'include'/n).read_bytes()).hexdigest() for n in ('wr-iot-timer-os-join.inc','wr-iot-timer-checked-join.inc')},
 'scope':'explicit timer-only process join; no peer cleanup caller or adapter/module lifetime proof',
 'target_compiled':False,'runtime_verified':False,'lifecycle_accepted':False,
},indent=2)+'\n')
print('Staged explicit timer process join with two OS syncs and queued-task drain')
