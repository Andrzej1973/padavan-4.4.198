#!/usr/bin/env python3
"""Reproduce vendor timer_pending guard skipping a running callback join.

This is a defect witness, NOT a successful timer-retirement acceptance test.
The extracted vendor function stays in local scratch output only.
"""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('candidate',type=Path);p.add_argument('output',type=Path)
p.add_argument('--cc',default='gcc')
a=p.parse_args();src=a.candidate.resolve(strict=True);out=a.output.resolve()
if out.exists() or src==out or src in out.parents or out in src.parents:
    p.error('new separate scratch output required')
path=src/'os/linux/rt_linux.c';text=path.read_text()
anchor='static inline VOID __RTMP_OS_Del_Timer('
if text.count(anchor)!=1:p.error('unreviewed timer function identity')
start=text.index(anchor);brace=text.index('{',start);depth=0
for end in range(brace,len(text)):
    if text[end]=='{':depth+=1
    elif text[end]=='}':
        depth-=1
        if not depth:break
body=text[start:end+1]
out.mkdir(parents=True)
prefix=r'''
#include <assert.h>
#include <stdio.h>
#define IN
#define OUT
#define TRUE 1
typedef void VOID;typedef int BOOLEAN;
typedef struct {int pending,running;} OS_NDIS_MINIPORT_TIMER;
static int joins;
static int timer_pending(OS_NDIS_MINIPORT_TIMER *t){return t->pending;}
static int del_timer_sync(OS_NDIS_MINIPORT_TIMER *t){int was=t->pending;joins++;t->running=t->pending=0;return was;}
'''
suffix=r'''
int main(void){OS_NDIS_MINIPORT_TIMER t={0,1};int cancelled=0;
__RTMP_OS_Del_Timer(&t,&cancelled);
assert(cancelled==1&&t.running==1&&joins==0);
t=(OS_NDIS_MINIPORT_TIMER){1,1};cancelled=0;joins=0;
__RTMP_OS_Del_Timer(&t,&cancelled);assert(cancelled==1&&!t.running&&joins==1);
puts("DEFECT REPRODUCED: running non-pending timer is reported cancelled without synchronization");return 0;}
'''
fixture=out/'timer-delete-witness.c';exe=out/'timer-delete-witness.exe'
fixture.write_text(prefix+body+suffix,encoding='utf-8',newline='\n')
subprocess.run([a.cc,'-std=c11','-O2','-Wall','-Wextra','-Werror',str(fixture),'-o',str(exe)],check=True)
subprocess.run([str(exe)],check=True)
report={'defect_reproduced':True,'timer_join_accepted':False,'target_compiled':False,
 'runtime_verified':False,'scope':'actual extracted branch with injected kernel timer states; not on-device race execution',
 'source':'os/linux/rt_linux.c','source_line':text[:start].count('\n')+1,
 'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
 'extracted_sha256':hashlib.sha256(body.encode()).hexdigest(),
 'finding':'running + not pending returns cancelled TRUE without del_timer_sync',
 'next':'process-context unconditional join with rearm fencing, timer-task running callback drain and caller lock audit'}
(out/'result.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
