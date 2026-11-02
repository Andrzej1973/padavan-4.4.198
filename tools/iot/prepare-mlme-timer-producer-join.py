#!/usr/bin/env python3
"""Join adapter-owned MLME timer producers before checked MLME cleanup."""
import argparse,hashlib,json,shutil
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
src=a.source.resolve(strict=True);out=a.output.resolve()
if out.exists() or src==out or src in out.parents or out in src.parents:p.error('new separate output required')
m=json.loads(src.with_name(src.name+'.manifest.json').read_text());actual={str(f.relative_to(src)):hashlib.sha256(f.read_bytes()).hexdigest() for f in src.rglob('*') if f.is_file()}
if actual!=m['merged_driver_sha256'] or m.get('production_installed') is not False or 'mlme_checked_halt_layer' not in m:p.error('changed/unsupported merged input')
name='common/mlme.c';s=(src/name).read_text()
old=' return wr_iot_mlme_halt_body(pAd, TRUE);'
new=''' /* Both timers are initialized by MlmeInit and embedded in the pinned
  * adapter. This checked close owns their lifecycle until later release-all.
  * Join the periodic command producer before its consumer is retired. */
 if (!wr_iot_timer_join_checked(pAd, &pAd->Mlme.PeriodicTimer, 5000UL) ||
     !wr_iot_timer_join_checked(pAd, &pAd->Mlme.RxAntEvalTimer, 5000UL))
  return FALSE;
 return wr_iot_mlme_halt_body(pAd, TRUE);'''
if s.count(old)!=1:p.error('unreviewed checked MLME wrapper')
changed=s.replace(old,new);assert changed.replace(new,old,1)==s
shutil.copytree(src,out);(out/name).write_text(changed);digest=hashlib.sha256((out/name).read_bytes()).hexdigest();m['merged_driver_sha256'][name]=digest;m['candidate_driver_sha256'][name]=digest
m.update(production_installed=False,target_compiled=False,runtime_verified=False)
m['mlme_timer_producer_join_layer']={'timers':['Mlme.PeriodicTimer','Mlme.RxAntEvalTimer'],'all_timers_retired':False,'target_compiled':False,'runtime_verified':False}
out.with_name(out.name+'.manifest.json').write_text(json.dumps(m,indent=2)+'\n')
print('Staged checked common MLME timer producer joins; remaining timer families unproven')
