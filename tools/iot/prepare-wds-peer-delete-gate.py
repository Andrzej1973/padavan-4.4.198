#!/usr/bin/env python3
"""Bind active WDS operation refusal before MAC peer deletion mutations."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('source',type=Path);p.add_argument('output',type=Path)
a=p.parse_args();src=a.source.resolve(strict=True);out=a.output.resolve()
if out.exists() or src==out or src in out.parents or out in src.parents:p.error('new separate output required')
rel='mgmt/mgmt_entrytb.c';raw=(src/rel).read_bytes()
pin='cad19a111ae8b59d98b1ba76279ef3de53ed95779e8bd4e639a7a09dd8eb7dcb'
if hashlib.sha256(raw).hexdigest()!=pin:p.error('unreviewed deletion input')
s=raw.decode();start=s.index('BOOLEAN MacTableDeleteEntry(');before=s[:start];body=s[start:]
anchor='\tpEntry = &pAd->MacTab.Content[wcid];\n\ttr_entry = &pAd->MacTab.tr_entry[wcid];'
assert body.count(anchor)==1
body=body.replace(anchor,anchor+'\n#include "wr-iot-wds-peer-delete-gate.inc"',1)
shutil.copytree(src,out);(out/rel).write_text(before+body,encoding='utf-8',newline='\n')
helper=Path(__file__).with_name('wds-peer-delete-gate.inc')
shutil.copyfile(helper,out/'include/wr-iot-wds-peer-delete-gate.inc')
out.with_name(out.name+'-peer-delete-gate.json').write_text(json.dumps({
 'input_sha256':pin,'output_sha256':hashlib.sha256((out/rel).read_bytes()).hexdigest(),
 'helper_sha256':hashlib.sha256(helper.read_bytes()).hexdigest(),
 'scope':'peer-deletion admission only; deferred retry and completion drain unbound',
 'target_compiled':False,'production_installed':False},indent=2)+'\n')
print('Staged WDS peer-delete admission before timer/vendor mutations')
