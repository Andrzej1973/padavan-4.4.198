#!/usr/bin/env python3
"""Bind retained no-write resume and exact-slot completion to lazy maintenance."""
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
receipt=json.loads(src.with_name(src.name+'-delete-resume.json').read_text())
for name,digest in receipt['output_sha256'].items():
    if hashlib.sha256((src/name).read_bytes()).hexdigest()!=digest:p.error('resume predecessor mismatch: '+name)
rel='include/wr-iot-wds-ageout-transaction.inc';raw=(src/rel).read_bytes();s=raw.decode()
anchor='static VOID wr_iot_wds_lazy_maintenance(RTMP_ADAPTER *pAd)'
if s.count(anchor)!=1:p.error('unreviewed lazy maintenance entry')
s=s.replace(anchor,'#include "wr-iot-wds-ageout-recovery.inc"\n\n'+anchor,1)
anchor='  BOOLEAN eligible = FALSE;'
if s.count(anchor)!=1:p.error('unreviewed maintenance loop')
s=s.replace(anchor,anchor+'\n  if (wr_iot_wds_recover_ageout(pAd, index)) continue;',1)
shutil.copytree(src,out)
(out/rel).write_text(s,encoding='utf-8',newline='\n')
helper=Path(__file__).with_name('wds-ageout-recovery.inc')
shutil.copyfile(helper,out/'include/wr-iot-wds-ageout-recovery.inc')
out.with_name(out.name+'-ageout-recovery.json').write_text(json.dumps({
 'input_sha256':hashlib.sha256(raw).hexdigest(),'output_sha256':hashlib.sha256((out/rel).read_bytes()).hexdigest(),
 'helper_sha256':hashlib.sha256(helper.read_bytes()).hexdigest(),
 'scope':'lazy maintenance NOT_WRITTEN continuation/slot finalizer; PARTIAL and DMA/TxS remain retained/unproven',
 'target_compiled':False,'production_installed':False,
},indent=2)+'\n')
print('Staged lazy WDS retained no-write recovery and exact-slot completion')
