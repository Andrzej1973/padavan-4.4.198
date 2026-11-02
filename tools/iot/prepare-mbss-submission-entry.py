#!/usr/bin/env python3
"""Install gated MBSS acquired-open submission entry; callback remains unbound."""
import argparse,hashlib,json,shutil
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
src=a.source.resolve(strict=True);out=a.output.resolve();here=Path(__file__).resolve().parent
if out.exists() or src==out or src in out.parents or out in src.parents:p.error('new separate output required')
m=json.loads(src.with_name(src.name+'.manifest.json').read_text());actual={str(f.relative_to(src)):hashlib.sha256(f.read_bytes()).hexdigest() for f in src.rglob('*') if f.is_file()}
if actual!=m['merged_driver_sha256'] or m.get('production_installed') is not False or 'mbss_reaper_gate_layer' not in m:p.error('changed/unsupported input')
changes={}
for rel,old,new in [
 ('include/rtmp.h','INT wr_iot_mbss_recovery_stop_join(RTMP_ADAPTER *ad);','INT wr_iot_mbss_recovery_stop_join(RTMP_ADAPTER *ad);\nINT wr_iot_mbss_recovery_submit(RTMP_ADAPTER *ad,PNET_DEV dev,unsigned long generation);'),
 ('common/rtmp_init.c','#include "wr-iot-mbss-recovery-stop.inc"','#include "wr-iot-mbss-recovery-stop.inc"\n#include "wr-iot-mbss-recovery-submit.inc"')]:
 s=(src/rel).read_text()
 if s.count(old)!=1:p.error('changed submission anchor: '+rel)
 changes[rel]=s.replace(old,new,1);assert changes[rel].replace(new,old,1)==s
asset='include/wr-iot-mbss-recovery-submit.inc'
if (src/asset).exists():p.error('unexpected existing helper')
shutil.copytree(src,out)
for rel,s in changes.items():(out/rel).write_text(s)
shutil.copyfile(here/'mbss-recovery-submit.inc',out/asset)
for rel in [*changes,asset]:
 digest=hashlib.sha256((out/rel).read_bytes()).hexdigest();m['merged_driver_sha256'][rel]=digest;m['candidate_driver_sha256'][rel]=digest
m.update(production_installed=False,target_compiled=False,runtime_verified=False)
m['mbss_submission_entry_layer']={'callback_bound':False,'ordinary_reap_bound':False,'target_compiled':False,'runtime_verified':False}
out.with_name(out.name+'.manifest.json').write_text(json.dumps(m,indent=2)+'\n')
print('Installed gated submission entry; close callback/ordinary reap remains unbound')
