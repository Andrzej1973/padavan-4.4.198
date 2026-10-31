#!/usr/bin/env python3
"""Fence WDS runtime slot mutation during registration/peer retirement."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('source',type=Path);p.add_argument('output',type=Path)
a=p.parse_args();src=a.source.resolve(strict=True);out=a.output.resolve()
if out.exists() or src==out or src in out.parents or out in src.parents:p.error('new separate output required')
rel='ap/ap_wds.c';raw=(src/rel).read_bytes()
receipt=json.loads(src.with_name(src.name+'-maintenance-refusal.json').read_text())
if hashlib.sha256(raw).hexdigest()!=receipt['output_sha256']:p.error('predecessor receipt mismatch')
s=raw.decode();start=s.index('INT WdsEntryAlloc(');end=s.index('VOID WdsEntryDel(',start)
body=s[start:end];anchor='\t\twds_entry = &pAd->WdsTab.WdsEntry[i];'
assert body.count(anchor)==1
body=body.replace(anchor,anchor+'\n#include "wr-iot-wds-slot-allocation-gate.inc"',1)
shutil.copytree(src,out);(out/rel).write_text(s[:start]+body+s[end:],encoding='utf-8',newline='\n')
helper=Path(__file__).with_name('wds-slot-allocation-gate.inc')
shutil.copyfile(helper,out/'include/wr-iot-wds-slot-allocation-gate.inc')
out.with_name(out.name+'-slot-allocation.json').write_text(json.dumps({
 'input_sha256':hashlib.sha256(raw).hexdigest(),'output_sha256':hashlib.sha256((out/rel).read_bytes()).hexdigest(),
 'helper_sha256':hashlib.sha256(helper.read_bytes()).hexdigest(),
 'scope':'runtime allocation admission only; age-out reservation not yet bound',
 'target_compiled':False,'production_installed':False},indent=2)+'\n')
print('Staged runtime WDS slot allocation gate; pre-netdev parsing preserved')
