#!/usr/bin/env python3
"""Bind staged MBSS delayed poll storage, lifetime guards and stop joining."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('source',type=Path);p.add_argument('output',type=Path)
a=p.parse_args();src=a.source.resolve(strict=True);out=a.output.resolve()
here=Path(__file__).resolve().parent
if out.exists() or src==out or src in out.parents or out in src.parents:
 p.error('new separate output required')
m=json.loads(src.with_name(src.name+'.manifest.json').read_text())
actual={str(f.relative_to(src)):hashlib.sha256(f.read_bytes()).hexdigest()
        for f in src.rglob('*') if f.is_file()}
if actual!=m['merged_driver_sha256'] or m.get('production_installed') is not False or 'mbss_submission_entry_layer' not in m:
 p.error('changed/unsupported input')
changes={};undo=[]
def one(rel,old,new):
 s=changes.get(rel,(src/rel).read_text())
 if s.count(old)!=1:p.error('changed caller anchor: '+rel)
 undo.append((rel,old,new));changes[rel]=s.replace(old,new,1)
one('include/rtmp.h','#include "mbss-reaper-gate.h"',
 '#include "mbss-reaper-gate.h"\n#include "mbss-poll-lifetime.h"')
one('include/rtmp.h',' struct wr_iot_mbss_reaper_gate wr_iot_mbss_reaper_gate;',
 ' struct wr_iot_mbss_reaper_gate wr_iot_mbss_reaper_gate;\n struct wr_iot_mbss_poll_lifetime wr_iot_mbss_poll_state;\n struct delayed_work wr_iot_mbss_poll_work;')
one('include/rtmp.h','INT wr_iot_mbss_recovery_poll(RTMP_ADAPTER *ad);',
 'INT wr_iot_mbss_recovery_poll(RTMP_ADAPTER *ad);\nINT wr_iot_mbss_poll_schedule(RTMP_ADAPTER *ad);\nINT wr_iot_mbss_poll_stop_join(RTMP_ADAPTER *ad);\nVOID wr_iot_mbss_poll_work_fn(struct work_struct *work);')
one('common/rtmp_init.c',' wr_iot_mbss_reaper_gate_init(&pAd->wr_iot_mbss_reaper_gate);',
 ' wr_iot_mbss_reaper_gate_init(&pAd->wr_iot_mbss_reaper_gate);\n wr_iot_mbss_poll_init(&pAd->wr_iot_mbss_poll_state);\n INIT_DELAYED_WORK(&pAd->wr_iot_mbss_poll_work,wr_iot_mbss_poll_work_fn);')
one('common/rtmp_init.c','#include "wr-iot-mbss-recovery-poll.inc"',
 '#include "wr-iot-mbss-recovery-poll.inc"\n#include "wr-iot-mbss-poll-caller.inc"')
one('common/rtmp_init.c','#include "wr-iot-mbss-poll-caller.inc"',
 '#include "wr-iot-mbss-poll-caller.inc"\n#include "wr-iot-mbss-recovery-handoff.inc"')
one('include/rtmp.h','INT wr_iot_mbss_poll_schedule(RTMP_ADAPTER *ad);',
 'INT wr_iot_mbss_poll_schedule(RTMP_ADAPTER *ad);\nINT wr_iot_mbss_recovery_handoff(RTMP_ADAPTER *ad,PNET_DEV dev,unsigned long generation,const struct wr_iot_radio_ticket *ticket);')
one('include/wr-iot-mbss-recovery-work.inc',
 ' if(!ad||!wr_iot_mbss_reaper_idle',
 ' if(!ad||ad->wr_iot_mbss_poll_state.pending||ad->wr_iot_mbss_poll_state.running||ad->wr_iot_mbss_poll_state.unjoined||work_busy(&ad->wr_iot_mbss_poll_work.work)||!wr_iot_mbss_reaper_idle')
one('include/wr-iot-mbss-recovery-stop.inc',
 ' if(!ad||wr_iot_os_join_context())return -1;',
 ' if(!ad||wr_iot_os_join_context())return -1;\n if(wr_iot_mbss_poll_stop_join(ad)!=0)return -1;')
one('include/rtmp.h','INT wr_iot_mbss_poll_stop_join(RTMP_ADAPTER *ad);',
 'INT wr_iot_mbss_poll_stop_join(RTMP_ADAPTER *ad);\nINT wr_iot_mbss_poll_join(RTMP_ADAPTER *ad);')
one('include/wr-iot-mbss-recovery-work.inc',
 'if(!ad||ad->wr_iot_mbss_poll_state.pending',
 'if(!ad||ad->wr_iot_mbss_poll_state.joining||ad->wr_iot_mbss_poll_state.pending')
restored=dict(changes)
for rel,old,new in reversed(undo):restored[rel]=restored[rel].replace(new,old,1)
assert all(s==(src/rel).read_text() for rel,s in restored.items())
assets={'include/wr-iot-mbss-recovery-handoff.inc':'mbss-recovery-handoff.inc',
        'include/mbss-poll-lifetime.h':'mbss-poll-lifetime.h',
        'include/wr-iot-mbss-poll-caller.inc':'mbss-poll-caller.inc'}
if any((src/rel).exists() for rel in assets):p.error('unexpected caller assets')
shutil.copytree(src,out)
for rel,s in changes.items():(out/rel).write_text(s)
for rel,name in assets.items():shutil.copyfile(here/name,out/rel)
for rel in [*changes,*assets]:
 digest=hashlib.sha256((out/rel).read_bytes()).hexdigest()
 m['merged_driver_sha256'][rel]=digest;m['candidate_driver_sha256'][rel]=digest
m.update(production_installed=False,target_compiled=False,runtime_verified=False)
m['mbss_poll_caller_layer']={'admission_bound':False,'target_compiled':False,'runtime_verified':False}
out.with_name(out.name+'.manifest.json').write_text(json.dumps(m,indent=2)+'\n')
print('Staged delayed poll caller; ordinary admission remains unbound')
