#!/usr/bin/env python3
"""Install historical loader abort after private thaw, without binding Method1."""
import argparse
import hashlib
import json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('source',type=Path)
p.add_argument('--install-isolated',action='store_true',required=True)
a=p.parse_args();src=a.source.resolve();mp=Path(str(src)+'.manifest.json')
raw=mp.read_bytes();m=json.loads(raw)
actual={str(f.relative_to(src)):hashlib.sha256(f.read_bytes()).hexdigest() for f in src.rglob('*') if f.is_file()}
if (m.get('production_installed') is not False or m.get('target_compiled') is not False
 or 'mcu_boot_thaw' not in m or 'mcu_boot_loader_abort' in m or actual!=m['merged_driver_sha256']):
 p.error('Expected unchanged isolated thaw candidate')
changes={}
for name,anchor,replacement in (
 ('include/mcu/andes_core.h','INT32 wr_iot_mcu_boot_thaw(struct _RTMP_ADAPTER *ad,const struct wr_iot_mcu_boot_ticket *ticket);',
  'INT32 wr_iot_mcu_boot_loader_abort(struct _RTMP_ADAPTER *ad,const struct wr_iot_mcu_boot_ticket *ticket);'),
 ('mcu/andes_core.c','#include "wr-iot-mcu-boot-thaw.inc"','#include "wr-iot-mcu-boot-loader-abort.inc"')):
 text=(src/name).read_text()
 if text.count(anchor)!=1:p.error('Changed thaw anchor: '+name)
 changes[name]=text.replace(anchor,anchor+'\n'+replacement)
changes['include/wr-iot-mcu-boot-loader-abort.inc']=Path(__file__).with_name('mcu-boot-loader-abort.inc').read_text()
for name,text in changes.items():(src/name).write_text(text)
hashes={name:hashlib.sha256((src/name).read_bytes()).hexdigest() for name in changes}
m['merged_driver_sha256'].update(hashes);m['candidate_driver_sha256'].update(hashes)
m['mcu_boot_loader_abort']={'input_manifest_sha256':hashlib.sha256(raw).hexdigest(),'output_sha256':hashes,
 'loader_bound':False,'target_compiled':False,'runtime_verified':False}
mp.write_text(json.dumps(m,indent=2)+'\n')
