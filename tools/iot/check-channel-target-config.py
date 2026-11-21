#!/usr/bin/env python3
"""Bind channel failure guards to actual MIPS objects and effective Kbuild flags."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--kernel', type=Path, required=True)
p.add_argument('--driver', type=Path, required=True)
p.add_argument('--compiler', type=Path, required=True)
p.add_argument('--manifest', type=Path, required=True)
p.add_argument('--output', type=Path, required=True)
a = p.parse_args()
raw = a.manifest.read_bytes()
manifest = json.loads(raw)
units = {'mt7603': 'chips/mt7603.c', 'cmm_asic_mt': 'hw_ctrl/cmm_asic_mt.c',
         'ap_autoChSel': 'ap/ap_autoChSel.c', 'rtmp_init_inf': 'common/rtmp_init_inf.c'}
reports = {}
a.output.parent.mkdir(parents=True, exist_ok=True)
for unit, relative in units.items():
    output = a.output.parent / ('channel-' + unit + '-config.json')
    subprocess.run([sys.executable, str(Path(__file__).with_name('check-task-config.py')),
                    '--kernel', str(a.kernel), '--driver', str(a.driver),
                    '--compiler', str(a.compiler), '--unit', unit,
                    '--output', str(output)], check=True)
    report = json.loads(output.read_text())
    required = ('MT7603', 'MT_MAC', 'RTMP_PCI_SUPPORT')
    if report['status'] != 'complete' or not all(report['macros'].get(n) for n in required):
        p.error('Channel guard disabled in actual translation unit: ' + unit)
    if report['source_sha256'] != manifest['merged_driver_sha256'][relative]:
        p.error('Channel translation unit differs from source manifest: ' + unit)
    obj = (a.driver / relative).with_suffix('.o')
    blob = obj.read_bytes()
    if (blob[:6] != b'\x7fELF\x01\x01' or
            int.from_bytes(blob[16:18], 'little') != 1 or
            int.from_bytes(blob[18:20], 'little') != 8):
        p.error('Expected ELF32 little-endian MIPS relocatable object: ' + unit)
    reports[unit] = {'source': relative, 'source_sha256': report['source_sha256'],
                     'command_sha256': report['command_sha256'],
                     'effective_macros': report['macros'],
                     'object_bytes': len(blob),
                     'object_sha256': hashlib.sha256(blob).hexdigest()}
a.output.write_text(json.dumps({
    'scope': 'Actual channel translation-unit objects and guard preprocessing',
    'manifest_sha256': hashlib.sha256(raw).hexdigest(), 'translation_units': reports,
    'target_objects_verified': True, 'runtime_verified': False,
}, indent=2) + '\n')
print('PASS channel guard macros/source binding and MIPS objects; not runtime proof')
