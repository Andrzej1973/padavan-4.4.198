#!/usr/bin/env python3
"""Join MBSS completion in PCI drain before accepting DRAINED; no admission."""
import argparse,hashlib,json,shutil
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
src=a.source.resolve(strict=True);out=a.output.resolve()
if out.exists() or src==out or src in out.parents or out in src.parents:p.error('new separate output required')
m=json.loads(src.with_name(src.name+'.manifest.json').read_text());actual={str(f.relative_to(src)):hashlib.sha256(f.read_bytes()).hexdigest() for f in src.rglob('*') if f.is_file()}
if actual!=m['merged_driver_sha256'] or m.get('production_installed') is not False or 'mbss_external_join_layer' not in m:p.error('changed/unsupported input')
rel='os/linux/pci_main_dev.c';original=(src/rel).read_text();start=original.index('static int wr_iot_pci_recovery_drain(');end=original.index('\n}',start)+2;s=original[start:end]
changes=[(' int next_pending, completed, preclosed;',' int next_pending, completed, preclosed, mbss_joined;'),('  wr_iot_main_recovery_join_complete(adapter);','  wr_iot_main_recovery_join_complete(adapter);\n  mbss_joined = wr_iot_mbss_recovery_join_completed(adapter) == 0;'),('    (adapter->wr_iot_main_recovery.deferred_owners ||','    (!mbss_joined || !wr_iot_mbss_recovery_idle_locked(adapter) ||\n     adapter->wr_iot_main_recovery.deferred_owners ||')]
body=s
for old,new in changes:
 if body.count(old)!=1:p.error('unreviewed PCI drain anchor')
 body=body.replace(old,new,1)
restored=body
for old,new in reversed(changes):restored=restored.replace(new,old,1)
assert restored==s
changed=original[:start]+body+original[end:]
shutil.copytree(src,out);(out/rel).write_text(changed);digest=hashlib.sha256((out/rel).read_bytes()).hexdigest();m['merged_driver_sha256'][rel]=digest;m['candidate_driver_sha256'][rel]=digest
m.update(production_installed=False,target_compiled=False,runtime_verified=False)
m['mbss_pci_drain_layer']={'admission_bound':False,'stop_join_bound':False,'target_compiled':False,'runtime_verified':False}
out.with_name(out.name+'.manifest.json').write_text(json.dumps(m,indent=2)+'\n')
print('Staged PCI MBSS join-before-DRAINED; admission/stop join still pending')
