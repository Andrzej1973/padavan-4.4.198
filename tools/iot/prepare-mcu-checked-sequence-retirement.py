#!/usr/bin/env python3
"""Consume checked IDs until verified epoch; no ledger reset or admission rearm."""
import argparse
import hashlib
import json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('source',type=Path)
p.add_argument('--install-isolated',action='store_true',required=True)
a=p.parse_args();src=a.source.resolve();mp=Path(str(src)+'.manifest.json')
raw=mp.read_bytes();manifest=json.loads(raw)
actual={str(f.relative_to(src)):hashlib.sha256(f.read_bytes()).hexdigest() for f in src.rglob('*') if f.is_file()}
if (manifest.get('production_installed') is not False or manifest.get('target_compiled') is not False or
    'mcu_boot_ring_transaction' not in manifest or 'mcu_checked_sequence_retirement' in manifest or
    actual!=manifest['merged_driver_sha256']):
 p.error('Expected unchanged isolated ring transaction candidate')
names=('include/mcu-sequence-reservation.h','mcu/andes_core.c')
changes={n:(src/n).read_text() for n in names}
def one(name,old,new):
 if changes[name].count(old)!=1:raise ValueError('Changed sequence retirement anchor: '+name+': '+old)
 changes[name]=changes[name].replace(old,new)
header='include/mcu-sequence-reservation.h'
one(header,'unsigned int occupied,cursor,poisoned,quarantined;',
    'unsigned int occupied,cursor,poisoned,quarantined,retired;')
one(header,'s->occupied|s->quarantined)', 's->occupied|s->quarantined|s->retired)')
one(header,'static inline int wr_iot_mcu_sequence_release(',
    Path(__file__).with_name('mcu-sequence-checked-retirement.inc').read_text()+'\nstatic inline int wr_iot_mcu_sequence_release(')
one('mcu/andes_core.c','slot=wr_iot_mcu_sequence_reserve(&ad->wr_iot_sequence);',
    'slot=msg->wr_iot_checked?wr_iot_mcu_sequence_reserve_checked(&ad->wr_iot_sequence):\n'
    '       wr_iot_mcu_sequence_reserve(&ad->wr_iot_sequence);')
for n,value in changes.items():(src/n).write_text(value)
hashes={n:hashlib.sha256((src/n).read_bytes()).hexdigest() for n in changes}
manifest['merged_driver_sha256'].update(hashes);manifest['candidate_driver_sha256'].update(hashes)
manifest['mcu_checked_sequence_retirement']={
 'input_manifest_sha256':hashlib.sha256(raw).hexdigest(),'output_sha256':hashes,
 'scope':'checked IDs never reused within retained ledger; exhaustion refuses, no epoch reset',
 'target_compiled':False,'runtime_verified':False,'firmware_epoch_verified':False}
mp.write_text(json.dumps(manifest,indent=2)+'\n')
