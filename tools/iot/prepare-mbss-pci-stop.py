#!/usr/bin/env python3
"""Install MBSS stop/join and guard PCI post-drain teardown paths."""
import argparse,hashlib,json,shutil
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
src=a.source.resolve(strict=True);out=a.output.resolve();here=Path(__file__).resolve().parent
if out.exists() or src==out or src in out.parents or out in src.parents:p.error('new separate output required')
m=json.loads(src.with_name(src.name+'.manifest.json').read_text());actual={str(f.relative_to(src)):hashlib.sha256(f.read_bytes()).hexdigest() for f in src.rglob('*') if f.is_file()}
if actual!=m['merged_driver_sha256'] or m.get('production_installed') is not False or 'mbss_pci_drain_layer' not in m:p.error('changed/unsupported input')
changes={};undo=[]
def one(rel,old,new):
 s=changes.get(rel,(src/rel).read_text())
 if s.count(old)!=1:p.error('unreviewed stop anchor '+rel)
 undo.append((rel,old,new));changes[rel]=s.replace(old,new,1)
one('include/rtmp.h','INT wr_iot_mbss_recovery_join_completed(RTMP_ADAPTER *ad);','INT wr_iot_mbss_recovery_join_completed(RTMP_ADAPTER *ad);\nINT wr_iot_mbss_recovery_stop_join(RTMP_ADAPTER *ad);')
one('common/rtmp_init.c','#include "wr-iot-mbss-recovery-join.inc"','#include "wr-iot-mbss-recovery-join.inc"\n#include "wr-iot-mbss-recovery-stop.inc"')
rel='os/linux/pci_main_dev.c';s=(src/rel).read_text();start=s.index('static VOID DEVEXIT rt_pci_remove(');end=s.index('\n}',start)+2;body=s[start:end]
anchor='wr_iot_main_recovery_join_complete(adapter);'
# Each existing synchronous main join in normal/stalled/post-detach path
# must also stop/join MBSS before its following return or release sequence.
if body.count(anchor)!=3:p.error('unreviewed PCI join path inventory')
changed=body.replace(anchor,anchor+'\n        if (wr_iot_mbss_recovery_stop_join(adapter) != 0) return;')
one(rel,body,changed)
restored=dict(changes)
for rel,old,new in reversed(undo):restored[rel]=restored[rel].replace(new,old,1)
assert all(s==(src/rel).read_text() for rel,s in restored.items())
asset='include/wr-iot-mbss-recovery-stop.inc'
if (src/asset).exists():p.error('unexpected stop helper')
shutil.copytree(src,out)
for rel,s in changes.items():(out/rel).write_text(s)
shutil.copyfile(here/'mbss-recovery-stop.inc',out/asset)
for rel in [*changes,asset]:
 digest=hashlib.sha256((out/rel).read_bytes()).hexdigest();m['merged_driver_sha256'][rel]=digest;m['candidate_driver_sha256'][rel]=digest
m.update(production_installed=False,target_compiled=False,runtime_verified=False)
m['mbss_pci_stop_layer']={'admission_bound':False,'external_serialization_proven':False,'target_compiled':False,'runtime_verified':False}
out.with_name(out.name+'.manifest.json').write_text(json.dumps(m,indent=2)+'\n')
print('Staged three PCI stop/join guards; admission/serialization still pending')
