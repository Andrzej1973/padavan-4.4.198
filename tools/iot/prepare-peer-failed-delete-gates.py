#!/usr/bin/env python3
"""Preserve failed insertion on normal deletion and observed reset refusal."""
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
receipt=json.loads(src.with_name(src.name+'-timer-checked-join.json').read_text())
for name,digest in receipt['output_sha256'].items():
    if hashlib.sha256((src/name).read_bytes()).hexdigest()!=digest:p.error('timer-join predecessor mismatch: '+name)
rel='mgmt/mgmt_entrytb.c';raw=(src/rel).read_bytes();s=raw.decode()
start=s.index('static BOOLEAN wr_iot_mac_delete_entry(');end=s.index('\n}',start)+2
body=s[start:end];anchor='if (wcid >= MAX_LEN_OF_MAC_TABLE)'
if body.count(anchor)!=1:p.error('unreviewed delete WCID bound')
body=body.replace(anchor,'if (wcid >= MAX_LEN_OF_MAC_TABLE || wcid >= MAX_LEN_OF_TR_TABLE)',1)
anchor='#include "wr-iot-wds-delete-resume-admission.inc"'
if body.count(anchor)!=1:p.error('unreviewed deletion admission')
body=body.replace(anchor,'#include "wr-iot-peer-failed-delete-gate.inc"\n'+anchor,1)
s=s[:start]+body+s[end:]
anchor='VOID MacTableReset(RTMP_ADAPTER *pAd, INT startWcid)'
if s.count(anchor)!=1:p.error('unreviewed full reset')
s=s.replace(anchor,'#include "wr-iot-peer-failed-reset-preflight.inc"\n\n'+anchor,1)
for signature,scope in [('VOID MacTableReset(', 'NULL'),('VOID MacTableResetWdev(', 'wdev')]:
    start=s.index(signature);end=s.index('\n}',start)+2;body=s[start:end]
    anchor='\tMAC_TABLE_ENTRY *pMacEntry;'
    if body.count(anchor)!=1:p.error('unreviewed reset declarations')
    body=body.replace(anchor,anchor+'\n\tif (wr_iot_reset_has_failed_setup(pAd,'+scope+')) return;',1)
    anchor='MacTableDeleteEntry(pAd, i, pMacEntry->Addr);'
    if body.count(anchor)!=1:p.error('unreviewed reset delete call')
    body=body.replace(anchor,'if (!MacTableDeleteEntry(pAd, i, pMacEntry->Addr)) return;',1)
    s=s[:start]+body+s[end:]
shutil.copytree(src,out)
(out/rel).write_text(s,encoding='utf-8',newline='\n')
for local,target in [('peer-failed-delete-gate.inc','wr-iot-peer-failed-delete-gate.inc'),('peer-failed-reset-preflight.inc','wr-iot-peer-failed-reset-preflight.inc')]:
    shutil.copyfile(Path(__file__).with_name(local),out/'include'/target)
out.with_name(out.name+'-failed-delete-gates.json').write_text(json.dumps({
 'input_sha256':hashlib.sha256(raw).hexdigest(),'output_sha256':hashlib.sha256((out/rel).read_bytes()).hexdigest(),
 'scope':'ordinary delete refusal and reset observation/abort; no atomic reset or parent failure propagation',
 'target_compiled':False,'runtime_verified':False,'lifecycle_accepted':False,
},indent=2)+'\n')
print('Staged failed-peer normal delete gate and reset refusal ordering')
