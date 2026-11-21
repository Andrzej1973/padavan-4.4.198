#!/usr/bin/env python3
"""Fence root reopen until recovery ownership and callbacks are retired."""
import argparse,hashlib,json,shutil
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
src=a.source.resolve(strict=True);out=a.output.resolve()
if out.exists() or src==out or src in out.parents or out in src.parents:p.error('new separate output required')
m=json.loads(src.with_name(src.name+'.manifest.json').read_text());actual={str(f.relative_to(src)):hashlib.sha256(f.read_bytes()).hexdigest() for f in src.rglob('*') if f.is_file()}
if actual!=m['merged_driver_sha256'] or m.get('production_installed') is not False or 'mlme_timer_producer_join_layer' not in m:p.error('changed/unsupported merged input')
name='os/linux/rt_main_dev.c';s=(src/name).read_text()
replacements=[('#include "virtual-open-claim.h"','#include "virtual-open-claim.h"\n#include "wr-iot-main-reopen-admission.h"'),(' admitted = net_dev == adapter->net_dev &&',''' admitted = net_dev == adapter->net_dev &&
  wr_iot_main_recovery_allows_reopen(&adapter->wr_iot_main_recovery,
   work_busy(&adapter->wr_iot_main_recovery_work),
   work_busy(&adapter->wr_iot_main_recovery_reap_work.work),
   adapter->wr_iot_aux_family_retry.deferred_owners,
   work_busy(&adapter->wr_iot_aux_family_retry_work)) &&''')]
changed=s
for old,new in replacements:
 if changed.count(old)!=1:p.error('unreviewed main-open anchor')
 changed=changed.replace(old,new)
restored=changed
for old,new in reversed(replacements):restored=restored.replace(new,old,1)
assert restored==s
helper='include/wr-iot-main-reopen-admission.h'
if (src/helper).exists():p.error('unexpected existing helper')
shutil.copytree(src,out);(out/name).write_text(changed);shutil.copyfile(Path(__file__).with_name('main-reopen-admission.h'),out/helper)
for rel in (name,helper):
 digest=hashlib.sha256((out/rel).read_bytes()).hexdigest();m['merged_driver_sha256'][rel]=digest;m['candidate_driver_sha256'][rel]=digest
m.update(production_installed=False,target_compiled=False,runtime_verified=False)
m['main_reopen_fence_layer']={'target_compiled':False,'runtime_verified':False,'rtnl_continuation_bound':False}
out.with_name(out.name+'.manifest.json').write_text(json.dumps(m,indent=2)+'\n')
print('Staged recovery-owner/callback main reopen fence; RTNL continuation remains unbound')
