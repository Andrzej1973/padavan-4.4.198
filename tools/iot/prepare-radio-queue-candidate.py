#!/usr/bin/env python3
"""Assemble disjoint queue/ACK changes, not a complete/buildable driver tree.

Source is read-only. manifest.json is written last; absent manifest means an
incomplete preparation. This utility never installs into firmware sources.
"""
import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

p=argparse.ArgumentParser()
p.add_argument('source',type=Path,help='exact pinned mt76x3 source directory')
p.add_argument('output',type=Path,help='new separate candidate bundle')
a=p.parse_args();root=a.source.resolve();out=a.output.resolve()
if out.exists() or out==root or root in out.parents or out in root.parents:
    raise SystemExit('Output must be new and separate')
here=Path(__file__).resolve().parent
groups={
 'enqueue':('prepare-checked-enqueue.py',['common/cmm_cmd.c','checked-enqueue.inc']),
 'queue':('prepare-queue-cleanup.py',['common/rtmp_init.c','os/linux/rt_rbus_pci_drv.c',
          'include/queued-result.h','include/queued-cleanup.h','include/queued-work.h']),
 'mcu':('prepare-mcu-radio-result.py',['include/mcu/andes_core.h',
        'mcu/andes_core.c','mcu/andes_mt.c','mcu/wr-iot-radio-result.h','checked-ack-branch.inc']),
}
source_names=['common/cmm_cmd.c','common/rtmp_init.c','os/linux/rt_rbus_pci_drv.c',
              'include/mcu/andes_core.h','mcu/andes_core.c','mcu/andes_mt.c']
originals={name:(root/name).read_bytes() for name in source_names}
inputs=[here/script for script,_ in groups.values()]
inputs += [here/name for name in ('queued-result.h','queued-cleanup.h','queued-work.h','radio-result.h')]
inputs += [here/'checked-radio-off-builder.inc']
tool_bytes={path:path.read_bytes() for path in inputs}
out.mkdir(parents=True)
records=[];seen=set();manifests={}
for group,(script,names) in groups.items():
    stage=out/'stages'/group
    stage.parent.mkdir(exist_ok=True)
    subprocess.run([sys.executable,str(here/script),str(root),str(stage)],check=True)
    manifests[group]=json.loads((stage/'manifest.json').read_text())
    if manifests[group]['production_installed'] is not False:
        raise SystemExit('Stage unexpectedly claims installation')
    for name in names:
        if name in seen:raise SystemExit('Overlapping stage output: '+name)
        seen.add(name);data=(stage/name).read_bytes()
        target=out/'driver'/name;target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(data)
        records.append({'path':name,'stage':group,
                        'purpose':'fixture' if name.endswith('.inc') else 'driver',
                        'sha256':hashlib.sha256(data).hexdigest()})
for name,data in originals.items():
    if (root/name).read_bytes()!=data:raise SystemExit('Source changed during assembly')
for path,data in tool_bytes.items():
    if path.read_bytes()!=data:raise SystemExit('Preparer/helper changed during assembly')
manifest={
 'schema':1,'source_revision':'c25283e915a2a00a763774dd255b14aff997285e',
 'source_git_blobs':{name:hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
                     for name,data in originals.items()},
 'complete_driver_tree':False,'production_installed':False,'issuer_bound':False,
 'radio_operation_bound':False,'target_compiled':False,'runtime_verified':False,
 'lifecycle_exclusion_proven':False,'files':records,'stage_manifests':manifests,
 'preparer_inputs':{path.name:hashlib.sha256(data).hexdigest() for path,data in tool_bytes.items()},
}
(out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
print('Assembled queue/ACK candidate changes; partial tree, no radio/production binding')
