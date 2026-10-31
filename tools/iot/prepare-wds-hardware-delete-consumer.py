#!/usr/bin/env python3
"""Propagate checked MT WDS hardware deletion failure before software release."""
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
receipt=json.loads(src.with_name(src.name+'-ageout-identity-owner.json').read_text())
for name,digest in receipt['output_sha256'].items():
    if hashlib.sha256((src/'include'/name).read_bytes()).hexdigest()!=digest:
        p.error('identity-owner predecessor mismatch: '+name)
rel='mgmt/mgmt_entrytb.c';raw=(src/rel).read_bytes()
pin='484a3f573d37da90445373e7fddd9ac0cd8c5d32a39012dded66e08bd140a504'
if hashlib.sha256(raw).hexdigest()!=pin:p.error('unreviewed peer deletion source')
s=raw.decode();start=s.index('BOOLEAN MacTableDeleteEntry(')
end=s.index('VOID MacTableReset',start);body=s[start:end]
anchor='RTMP_STA_ENTRY_MAC_RESET(pAd, wcid);'
if body.count(anchor)!=1:p.error('unreviewed hardware-delete call')
body=body.replace(anchor,'\n#include "wr-iot-wds-hardware-delete-result.inc"',1)
body='#include "wr-iot-wds-hardware-delete-observer.inc"\n\n'+body
shutil.copytree(src,out)
(out/rel).write_text(s[:start]+body+s[end:],encoding='utf-8',newline='\n')
helper=Path(__file__).with_name('wds-hardware-delete-result.inc')
shutil.copyfile(helper,out/'include/wr-iot-wds-hardware-delete-result.inc')
observer=Path(__file__).with_name('wds-hardware-delete-observer.inc')
shutil.copyfile(observer,out/'include/wr-iot-wds-hardware-delete-observer.inc')
owner=Path(__file__).with_name('wds-peer-operation.h')
shutil.copyfile(owner,out/'include/wds-peer-operation.h')
delete_gate=Path(__file__).with_name('wds-peer-delete-gate.inc')
shutil.copyfile(delete_gate,out/'include/wr-iot-wds-peer-delete-gate.inc')
out.with_name(out.name+'-hardware-delete-consumer.json').write_text(json.dumps({
 'input_sha256':pin,'output_sha256':hashlib.sha256((out/rel).read_bytes()).hexdigest(),
 'helper_sha256':hashlib.sha256(helper.read_bytes()).hexdigest(),
 'observer_sha256':hashlib.sha256(observer.read_bytes()).hexdigest(),
 'owner_sha256':hashlib.sha256(owner.read_bytes()).hexdigest(),
 'delete_gate_sha256':hashlib.sha256(delete_gate.read_bytes()).hexdigest(),
 'scope':'WDS MT hardware deletion refusal before software release; no partial retry or DMA join',
 'target_compiled':False,'production_installed':False,
},indent=2)+'\n')
print('Staged checked WDS hardware deletion consumer')
