#!/usr/bin/env python3
"""Repair one invalid-BSS insertion lock leak in isolated source only."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('source', type=Path)
p.add_argument('output', type=Path)
a = p.parse_args()
src = a.source.resolve(strict=True)
out = a.output.resolve()
if out.exists() or src == out or src in out.parents or out in src.parents:
    p.error('new separate output required')
rel = 'mgmt/mgmt_entrytb.c'
raw = (src / rel).read_bytes()
pin = 'b38e1c045c02a38a34f10154664336c2c3341ec1b4c4c41d3f8f8b200daaa055'
if hashlib.sha256(raw).hexdigest() != pin:
    p.error('unreviewed insertion source')
s = raw.decode()
old = '\t\t\t\t\tif (pEntry->func_tb_idx >= HW_BEACON_MAX_NUM)\n\t\t\t\t\t\treturn NULL;'
new = '\t\t\t\t\tif (pEntry->func_tb_idx >= HW_BEACON_MAX_NUM) {\n\t\t\t\t\t\tNdisReleaseSpinLock(&pAd->MacTabLock);\n\t\t\t\t\t\treturn NULL;\n\t\t\t\t\t}'
if s.count(old) != 1:
    p.error('unique invalid-BSS failure required')
shutil.copytree(src, out)
(out / rel).write_text(s.replace(old, new, 1), encoding='utf-8', newline='\n')
out.with_name(out.name + '-bss-unlock.json').write_text(json.dumps({
    'input_sha256': {rel: pin},
    'output_sha256': {rel: hashlib.sha256((out / rel).read_bytes()).hexdigest()},
    'scope': 'one insertion lock leak; WTBL failure/reuse still open',
    'production_installed': False, 'target_compiled': False
}, indent=2) + '\n', encoding='utf-8')
print('Staged invalid-BSS unlock; no production installation')
