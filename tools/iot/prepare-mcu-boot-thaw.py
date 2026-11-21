#!/usr/bin/env python3
"""Install private command thaw into an unchanged isolated retirement candidate."""
import argparse
import hashlib
import json
from pathlib import Path

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('source',type=Path)
p.add_argument('--install-isolated',action='store_true',required=True)
a=p.parse_args();src=a.source.resolve();mp=Path(str(src)+'.manifest.json')
raw=mp.read_bytes();m=json.loads(raw)
actual={str(f.relative_to(src)):hashlib.sha256(f.read_bytes()).hexdigest()
        for f in src.rglob('*') if f.is_file()}
if (m.get('production_installed') is not False or m.get('target_compiled') is not False
    or 'mcu_boot_retired_boundary' not in m or 'mcu_boot_thaw' in m
    or actual!=m['merged_driver_sha256']):
 p.error('Expected unchanged isolated retirement-boundary candidate')
changes={}
name='include/mcu/andes_core.h';text=(src/name).read_text()
anchor='INT32 wr_iot_mcu_boot_retired_boundary(struct _RTMP_ADAPTER *ad,const struct wr_iot_mcu_boot_ticket *ticket);'
if text.count(anchor)!=1:p.error('Changed retirement declaration')
changes[name]=text.replace(anchor,anchor+'\nINT32 wr_iot_mcu_boot_thaw(struct _RTMP_ADAPTER *ad,const struct wr_iot_mcu_boot_ticket *ticket);')
name='mcu/andes_core.c';text=(src/name).read_text();anchor='#include "wr-iot-mcu-boot-retired-boundary.inc"'
if text.count(anchor)!=1:p.error('Changed retirement include')
changes[name]=text.replace(anchor,anchor+'\n#include "wr-iot-mcu-boot-thaw.inc"')
changes['include/wr-iot-mcu-boot-thaw.inc']=Path(__file__).with_name('mcu-boot-thaw.inc').read_text()
for name,text in changes.items():(src/name).write_text(text)
hashes={name:hashlib.sha256((src/name).read_bytes()).hexdigest() for name in changes}
m['merged_driver_sha256'].update(hashes);m['candidate_driver_sha256'].update(hashes)
m['mcu_boot_thaw']={'input_manifest_sha256':hashlib.sha256(raw).hexdigest(),
 'output_sha256':hashes,'scope':'private command constructor thaw after hardware and retirement receipt',
 'loader_bound':False,'target_compiled':False,'runtime_verified':False}
mp.write_text(json.dumps(m,indent=2)+'\n')
