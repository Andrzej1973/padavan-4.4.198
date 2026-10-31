#!/usr/bin/env python3
"""Inventory peer timer initialization/arming without assuming callback quiescence."""
import argparse
import hashlib
import json
import re
from pathlib import Path

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('candidate',type=Path);p.add_argument('output',type=Path)
a=p.parse_args();src=a.candidate.resolve(strict=True)
if a.output.exists():p.error('new report required')

def scrub(text):
    # Preserve offsets/newlines; ignore comment/string pseudo-call sites.
    pattern=r'/\*.*?\*/|//[^\n]*|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\''
    return re.sub(pattern,lambda m:''.join('\n' if c=='\n' else ' ' for c in m.group()),text,flags=re.S)

def function(text,anchor):
    if text.count(anchor)!=1:raise ValueError('non-unique function: '+anchor)
    start=text.index(anchor);brace=text.index('{',start);depth=0
    for end in range(brace,len(text)):
        if text[end]=='{':depth+=1
        elif text[end]=='}':
            depth-=1
            if not depth:return text[start:end+1]
    raise ValueError('unterminated function')

names=('RTMPInitTimer','RTMPSetTimer','RTMPModTimer','RTMP_OS_Add_Timer',
       'RTMP_OS_Mod_Timer','RTMP_SetPeriodicTimer','RtmpTimerQInsert')
timers=('EnqueueStartForPSKTimer','RetryTimer','SAQueryTimer',
        'SAQueryConfirmTimer','EapReqIdRetryTimer')
calls=[];hashes={}
for path in sorted(src.rglob('*')):
    if path.suffix not in ('.c','.h') or 'check-' in path.name:continue
    raw=path.read_bytes();text=scrub(raw.decode(errors='replace'))
    for match in re.finditer(r'\b('+'|'.join(names)+r')\s*\(',text):
        begin=match.end();depth=1
        for end in range(begin,len(text)):
            if text[end]=='(':depth+=1
            elif text[end]==')':
                depth-=1
                if not depth:break
        args=text[begin:end]
        fields=[t for t in timers if re.search(r'\b'+t+r'\b',args)]
        if fields:
            rel=path.relative_to(src).as_posix()
            hashes[rel]=hashlib.sha256(raw).hexdigest()
            calls.append({'file':rel,'line':text[:match.start()].count('\n')+1,
                          'api':match.group(1),'timer_fields':fields})
entry=scrub((src/'mgmt/mgmt_entrytb.c').read_text())
entry=function(entry,'MAC_TABLE_ENTRY *wr_iot_mac_insert_entry(')
init=function(scrub((src/'common/rtmp_init.c').read_text()),'VOID RTMPInitTimer(')
linux_init=function(scrub((src/'os/linux/rt_linux.c').read_text()),'static inline VOID __RTMP_OS_Init_Timer(')
arm_names=names[1:-1]
assert not any(re.search(r'\b'+n+r'\s*\(',entry) for n in arm_names)
assert not any(re.search(r'\b'+n+r'\s*\(',init) for n in arm_names)
assert not re.search(r'\b(?:add_timer|mod_timer)\s*\(',linux_init)
report={'scope':'literal source inventory, feature branches not preprocessed; aliases/transitive callers not proven',
 'insertion_init_calls':len(re.findall(r'\bRTMPInitTimer\s*\(',entry)),
 'insertion_direct_arm_calls':0,'RTMPInitTimer_arms_directly':False,
 'linux_timer_init_arms_directly':False,'peer_timer_calls':calls,'source_sha256':hashes,
 'cleanup_accepted':False,'runtime_verified':False,
 'open':['array readers may obtain unpublished entries','old WCID/timer reuse must be excluded',
         'transitive/raw alias arming','executing callback/task join and rearm fence']}
a.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print('Inventory: '+str(len(calls))+' peer-timer init/arm sites; '+str(report['insertion_init_calls'])+' insertion init sites, no direct insertion arm; cleanup NOT accepted')
