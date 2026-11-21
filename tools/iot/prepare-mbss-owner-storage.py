#!/usr/bin/env python3
"""Bind fresh per-slot MBSS owner storage and initialized release/reopen gates.

No worker admission yet: direct-free/PCI/work joins still need binding.
"""
import argparse,hashlib,json,shutil
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
src=a.source.resolve(strict=True);out=a.output.resolve();here=Path(__file__).resolve().parent
if out.exists() or src==out or src in out.parents or out in src.parents:p.error('new separate output required')
m=json.loads(src.with_name(src.name+'.manifest.json').read_text());actual={str(f.relative_to(src)):hashlib.sha256(f.read_bytes()).hexdigest() for f in src.rglob('*') if f.is_file()}
if actual!=m['merged_driver_sha256'] or m.get('production_installed') is not False or 'main_physical_close_delegation_layer' not in m:p.error('changed/unsupported input')
changes={};undo=[]
def one(rel,old,new):
 s=changes.get(rel,(src/rel).read_text())
 if s.count(old)!=1:p.error('unreviewed storage anchor: '+rel)
 undo.append((rel,old,new));changes[rel]=s.replace(old,new,1)
one('include/rtmp.h','#include "main-open-recovery-owner.h"','#include "main-open-recovery-owner.h"\n#include "mbss-recovery-storage.h"')
one('include/rtmp.h','\tstruct wr_iot_main_recovery_owner wr_iot_main_recovery;','\tstruct wr_iot_main_recovery_owner wr_iot_main_recovery;\n struct wr_iot_mbss_recovery_owner wr_iot_mbss_recovery[WDEV_NUM_MAX + 1];')
one('common/rtmp_init.c',' wr_iot_family_close_init(&pAd->wr_iot_family_close[wr_iot_slot]);}', ' wr_iot_family_close_init(&pAd->wr_iot_family_close[wr_iot_slot]);\n wr_iot_mbss_recovery_init(&pAd->wr_iot_mbss_recovery[wr_iot_slot]);}')
one('include/wr-iot-peer-adapter-release.inc','  !pAd->wr_iot_registration_inflight && !pAd->wr_iot_main_recovery.deferred_owners &&', '  !pAd->wr_iot_registration_inflight && !pAd->wr_iot_main_recovery.deferred_owners &&\n  wr_iot_mbss_recovery_storage_idle(pAd->wr_iot_mbss_recovery,WDEV_NUM_MAX+1) &&')
one('os/linux/rt_main_dev.c',' admitted = net_dev == adapter->net_dev &&',' admitted = net_dev == adapter->net_dev &&\n  wr_iot_mbss_recovery_storage_idle(adapter->wr_iot_mbss_recovery,WDEV_NUM_MAX+1) &&')
assets=['mbss-close-recovery-owner.h','mbss-recovery-storage.h']
for rel in assets:
 f=src/'include'/rel
 if f.exists() and f.read_bytes()!=(here/rel).read_bytes():p.error('changed existing owner asset: '+rel)
restored=dict(changes)
for rel,old,new in reversed(undo):restored[rel]=restored[rel].replace(new,old,1)
assert all(s==(src/rel).read_text() for rel,s in restored.items())
shutil.copytree(src,out)
for rel,s in changes.items():(out/rel).write_text(s)
for rel in assets:shutil.copyfile(here/rel,out/'include'/rel)
for rel in [*changes,*['include/'+f for f in assets]]:
 digest=hashlib.sha256((out/rel).read_bytes()).hexdigest();m['merged_driver_sha256'][rel]=digest;m['candidate_driver_sha256'][rel]=digest
m.update(production_installed=False,target_compiled=False,runtime_verified=False)
m['mbss_owner_storage_layer']={'worker_dispatched':False,'all_free_paths_bound':False,'target_compiled':False,'runtime_verified':False}
out.with_name(out.name+'.manifest.json').write_text(json.dumps(m,indent=2)+'\n')
print('Staged per-slot MBSS storage/reopen/initialized release fence; worker unbound')
