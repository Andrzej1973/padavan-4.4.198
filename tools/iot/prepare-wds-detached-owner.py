#!/usr/bin/env python3
"""Stage retained post-unregister WDS ownership; completion/reaper still required."""
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
pin='302dc092c42aa48829ada8d8674466087ec6e9f0352c4d939afd363d9053eb93'
if hashlib.sha256(raw).hexdigest()!=pin:p.error('unreviewed WDS input')
s=raw.decode()
old='''\t\t\trtmp_wdev_idx_unreg(pAd, wdev);
\t\t\tRtmpOSNetDevFree(wdev->if_dev);

\t\t\t/* Clear it as NULL to prevent latter access error. */
\t\t\twdev->if_dev = NULL;'''
assert s.count(old)==1
new='''\t\t\t/* Retain allocation and vendor registration until callback retirement.
\t\t\t * Existing removing flag rejects a second unregister attempt. */
\t\t\t{
\t\t\t\tULONG flags;
\t\t\t\tUINT slot;
\t\t\t\tRTMP_IRQ_LOCK(&pAd->wr_iot_transition_lock, flags);
\t\t\t\tfor (slot = 0; slot < WDEV_NUM_MAX + 1; slot++) {
\t\t\t\t\tstruct wr_iot_interface_ref *record = &pAd->wr_iot_interface_refs[slot];
\t\t\t\t\tif (record->device == wdev->if_dev) {
\t\t\t\t\t\t(void)wr_iot_registry_after_unregister(record, wdev->if_dev,
\t\t\t\t\t\t    record->generation, 1);
\t\t\t\t\t\tbreak;
\t\t\t\t\t}
\t\t\t\t}
\t\t\t\tRTMP_IRQ_UNLOCK(&pAd->wr_iot_transition_lock, flags);
\t\t\t}
\t\t\treturn NDIS_STATUS_FAILURE; /* Retained; callback join/reaper not bound. */'''
s=s.replace(old,new,1)
shutil.copytree(src,out);(out/rel).write_text(s,encoding='utf-8',newline='\n')
out.with_name(out.name+'-wds-owner.json').write_text(json.dumps({
 'input_sha256':pin,'output_sha256':hashlib.sha256((out/rel).read_bytes()).hexdigest(),
 'scope':'retained post-unregister allocation only; no callback join/reaper',
 'production_installed':False,'target_compiled':False,'removal_completed':False},indent=2)+'\n')
print('Staged WDS detached allocation owner; removal intentionally incomplete until reaper binding')
