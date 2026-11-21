#!/usr/bin/env python3
"""Save exact WDS retirement identity before deletion and retain it on failure."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('source',type=Path);p.add_argument('output',type=Path)
a=p.parse_args();src=a.source.resolve(strict=True);out=a.output.resolve()
if out.exists() or src==out or src in out.parents or out in src.parents:
    p.error('new separate output required')
receipt=json.loads(src.with_name(src.name+'-wds-lock-lifetime.json').read_text())
for name,digest in receipt['output_sha256'].items():
    if hashlib.sha256((src/name).read_bytes()).hexdigest()!=digest:
        p.error('lock-lifetime predecessor mismatch: '+name)
helpers={'wds-peer-operation.h':'wds-peer-operation.h',
         'wds-ageout-transaction.inc':'wr-iot-wds-ageout-transaction.inc'}
shutil.copytree(src,out)
for local,target in helpers.items():
    shutil.copyfile(Path(__file__).with_name(local),out/'include'/target)
out.with_name(out.name+'-ageout-identity-owner.json').write_text(json.dumps({
 'predecessor':receipt['output_sha256'],
 'output_sha256':{target:hashlib.sha256((out/'include'/target).read_bytes()).hexdigest() for target in helpers.values()},
 'scope':'saved synchronous retirement identity/retained failure; recovery continuation not bound',
 'target_compiled':False,'production_installed':False,
},indent=2)+'\n')
print('Staged persistent WDS age-out identity and non-reused serial')
