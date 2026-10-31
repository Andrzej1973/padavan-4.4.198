#!/usr/bin/env python3
"""Compose WDS insertion gate and current-peer admission closure, no retirement proof."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('source',type=Path);p.add_argument('output',type=Path)
a=p.parse_args();src=a.source.resolve(strict=True);out=a.output.resolve()
if out.exists() or src==out or src in out.parents or out in src.parents:p.error('new separate output required')
pins={'ap/ap_wds.c':'29094b4335e3abaf1da9421756e2eb52e6316c8407f391de4ad290139c72ec37',
      'mgmt/mgmt_entrytb.c':'22d4ec4887ada52b6f09fc86d9a8b9c43b0ea4ab4783ddb65446d11ef8432db6'}
for n,h in pins.items():
    if hashlib.sha256((src/n).read_bytes()).hexdigest()!=h:p.error('unreviewed source: '+n)
here=Path(__file__).resolve().parent
s=(src/'mgmt/mgmt_entrytb.c').read_text();begin=s.index('MAC_TABLE_ENTRY *MacTableInsertEntry(')
before=s[:begin];body=s[begin:];anchor='\t/* allocate one MAC entry*/\n\tNdisAcquireSpinLock(&pAd->MacTabLock);'
assert body.count(anchor)==1
body=body.replace(anchor,anchor+'\n#include "wr-iot-wds-insertion-gate.inc"',1)
mgmt=before+body
s=(src/'ap/ap_wds.c').read_text();anchor='INT WDS_Remove(RTMP_ADAPTER *pAd)'
assert s.count(anchor)==1
s=s.replace(anchor,'#include "wr-iot-wds-peer-admission.inc"\n\n'+anchor,1)
anchor='\t\t\tRtmpOSNetDevProtect(1);'
begin=s.index('INT WDS_Remove(');before=s[:begin];body=s[begin:]
assert body.count(anchor)==1
body=body.replace(anchor,'\t\t\tif (wr_iot_wds_block_peer_admission(pAd, wdev) != NDIS_STATUS_SUCCESS)\n\t\t\t\treturn NDIS_STATUS_FAILURE;\n'+anchor,1)
shutil.copytree(src,out)
for n,t in [('mgmt/mgmt_entrytb.c',mgmt),('ap/ap_wds.c',before+body)]:
    (out/n).write_text(t,encoding='utf-8',newline='\n')
for n in ['wds-insertion-gate.inc','wds-peer-admission.inc']:
    shutil.copyfile(here/n,out/'include'/('wr-iot-'+n))
out.with_name(out.name+'-peer-fence.json').write_text(json.dumps({
    'input_sha256':pins,'scope':'current insertion/removal admission only; retained completion/reaper absent',
    'target_compiled':False,'production_installed':False},indent=2)+'\n')
print('Staged WDS insertion/removal peer admission fence; no completion drain proof')
