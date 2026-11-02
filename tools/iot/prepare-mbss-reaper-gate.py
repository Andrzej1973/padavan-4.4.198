#!/usr/bin/env python3
"""Bind permanent MBSS submission fence and exclusive external reaper lease."""
import argparse,hashlib,json,shutil
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
src=a.source.resolve(strict=True);out=a.output.resolve();here=Path(__file__).resolve().parent
if out.exists() or src==out or src in out.parents or out in src.parents:p.error('new separate output required')
m=json.loads(src.with_name(src.name+'.manifest.json').read_text());actual={str(f.relative_to(src)):hashlib.sha256(f.read_bytes()).hexdigest() for f in src.rglob('*') if f.is_file()}
if actual!=m['merged_driver_sha256'] or m.get('production_installed') is not False or 'mbss_pci_stop_layer' not in m:p.error('changed/unsupported input')
changes={};undo=[]
def one(rel,old,new):
 s=changes.get(rel,(src/rel).read_text())
 if s.count(old)!=1:p.error('unreviewed reaper anchor '+rel)
 undo.append((rel,old,new));changes[rel]=s.replace(old,new,1)
one('include/rtmp.h','#include "mbss-recovery-storage.h"','#include "mbss-recovery-storage.h"\n#include "mbss-reaper-gate.h"')
one('include/rtmp.h',' unsigned int wr_iot_recovery_storage_live;',' unsigned int wr_iot_recovery_storage_live;\n struct wr_iot_mbss_reaper_gate wr_iot_mbss_reaper_gate;')
one('common/rtmp_init.c','\t\twr_iot_main_recovery_init(&pAd->wr_iot_main_recovery);','\t\twr_iot_main_recovery_init(&pAd->wr_iot_main_recovery);\n wr_iot_mbss_reaper_gate_init(&pAd->wr_iot_mbss_reaper_gate);')
one('include/wr-iot-mbss-recovery-work.inc',' if(!ad||!wr_iot_mbss_recovery_storage_idle',' if(!ad||!wr_iot_mbss_reaper_idle(&ad->wr_iot_mbss_reaper_gate)||!wr_iot_mbss_recovery_storage_idle')
# Inner join runs under the caller-owned reaper lease, so test owners/work
# directly instead of the public idle gate which must reject a live reaper.
rel='include/wr-iot-mbss-recovery-join.inc'
one(rel,'INT wr_iot_mbss_recovery_join_completed(RTMP_ADAPTER *ad)','static INT wr_iot_mbss_recovery_join_owned(RTMP_ADAPTER *ad)')
one(rel,' ready=wr_iot_mbss_recovery_idle_locked(ad);',' ready=wr_iot_mbss_recovery_storage_idle(ad->wr_iot_mbss_recovery,WDEV_NUM_MAX+1);\n for(slot=0;ready&&slot<WDEV_NUM_MAX+1;slot++)\n  if(work_busy(&ad->wr_iot_mbss_work[slot].work))ready=0;')
wrapper='''
INT wr_iot_mbss_recovery_join_completed(RTMP_ADAPTER *ad)
{
 ULONG flags;int entered,result;
 if(!ad||wr_iot_os_join_context())return -1;
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 entered=wr_iot_mbss_reaper_enter(&ad->wr_iot_mbss_reaper_gate);
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 if(!entered)return -1;
 result=wr_iot_mbss_recovery_join_owned(ad);
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 if(!wr_iot_mbss_reaper_leave(&ad->wr_iot_mbss_reaper_gate))result=-1;
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 return result;
}
'''
base=changes[rel];one(rel,base,base+wrapper)
rel='include/wr-iot-mbss-recovery-stop.inc'
one(rel,' ULONG flags;',' ULONG flags;int entered,result;')
one(rel,' for(slot=0;slot<WDEV_NUM_MAX+1;slot++)\n  (void)wr_iot_mbss_recovery_request_stop', ' wr_iot_mbss_reaper_stop(&ad->wr_iot_mbss_reaper_gate);\n entered=wr_iot_mbss_reaper_enter(&ad->wr_iot_mbss_reaper_gate);\n if(!entered){RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);return -1;}\n for(slot=0;slot<WDEV_NUM_MAX+1;slot++)\n  (void)wr_iot_mbss_recovery_request_stop')
one(rel,' return wr_iot_mbss_recovery_join_completed(ad);',' result=wr_iot_mbss_recovery_join_owned(ad);\n RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);\n if(!wr_iot_mbss_reaper_leave(&ad->wr_iot_mbss_reaper_gate))result=-1;\n RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);\n return result;')
restored=dict(changes)
for rel,old,new in reversed(undo):restored[rel]=restored[rel].replace(new,old,1)
assert all(s==(src/rel).read_text() for rel,s in restored.items())
asset='include/mbss-reaper-gate.h'
if (src/asset).exists():p.error('unexpected gate')
shutil.copytree(src,out)
for rel,s in changes.items():(out/rel).write_text(s)
shutil.copyfile(here/'mbss-reaper-gate.h',out/asset)
for rel in [*changes,asset]:
 digest=hashlib.sha256((out/rel).read_bytes()).hexdigest();m['merged_driver_sha256'][rel]=digest;m['candidate_driver_sha256'][rel]=digest
m.update(production_installed=False,target_compiled=False,runtime_verified=False)
m['mbss_reaper_gate_layer']={'admission_bound':False,'target_compiled':False,'runtime_verified':False}
out.with_name(out.name+'.manifest.json').write_text(json.dumps(m,indent=2)+'\n')
print('Staged adapter gate and serialized join/stop; submission still unbound')
