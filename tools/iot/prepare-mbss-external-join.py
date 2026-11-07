#!/usr/bin/env python3
"""Install external MBSS join helper; admission/PCI callers remain unbound."""
import argparse,hashlib,json,shutil
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
src=a.source.resolve(strict=True);out=a.output.resolve();here=Path(__file__).resolve().parent
if out.exists() or src==out or src in out.parents or out in src.parents:p.error('new separate output required')
m=json.loads(src.with_name(src.name+'.manifest.json').read_text());actual={str(f.relative_to(src)):hashlib.sha256(f.read_bytes()).hexdigest() for f in src.rglob('*') if f.is_file()}
if actual!=m['merged_driver_sha256'] or m.get('production_installed') is not False or 'mbss_work_binding_layer' not in m:p.error('changed/unsupported input')
changes={}
for rel,old,new in [
 ('include/rtmp.h','BOOLEAN wr_iot_mbss_recovery_idle_locked(RTMP_ADAPTER *ad);','BOOLEAN wr_iot_mbss_recovery_idle_locked(RTMP_ADAPTER *ad);\nINT wr_iot_mbss_recovery_join_completed(RTMP_ADAPTER *ad);'),
 ('common/rtmp_init.c','#include "wr-iot-mbss-recovery-work.inc"','#include "wr-iot-mbss-recovery-work.inc"\n#include "wr-iot-mbss-recovery-join.inc"')]:
 s=(src/rel).read_text()
 if s.count(old)!=1:p.error('changed join anchor: '+rel)
 changes[rel]=s.replace(old,new,1);assert changes[rel].replace(new,old,1)==s
asset='include/wr-iot-mbss-recovery-join.inc'
if (src/asset).exists():p.error('unexpected existing helper')
shutil.copytree(src,out)
for rel,s in changes.items():(out/rel).write_text(s)
shutil.copyfile(here/'mbss-recovery-join.inc',out/asset)
for rel in [*changes,asset]:
 digest=hashlib.sha256((out/rel).read_bytes()).hexdigest();m['merged_driver_sha256'][rel]=digest;m['candidate_driver_sha256'][rel]=digest
m.update(production_installed=False,target_compiled=False,runtime_verified=False)
m['mbss_external_join_layer']={'pci_caller_bound':False,'admission_bound':False,'target_compiled':False,'runtime_verified':False}
out.with_name(out.name+'.manifest.json').write_text(json.dumps(m,indent=2)+'\n')
print('Installed external MBSS join entry; caller/admission remains unbound')
