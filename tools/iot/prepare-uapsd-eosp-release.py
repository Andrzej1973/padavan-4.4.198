#!/usr/bin/env python3
"""Repair three stale EOSP pointers in isolated deletion-join successor."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('source', type=Path)
p.add_argument('output', type=Path)
a = p.parse_args()
source = a.source.resolve(strict=True)
out = a.output.resolve()
if out.exists() or source == out or source in out.parents or out in source.parents:
    p.error('new separate output required')
rel = 'common/uapsd.c'
raw = (source / rel).read_bytes()
pin = '5f00569b22c0975619034290c15099552b6d84c6af9aafeaa5a6d05a89fc9770'
if hashlib.sha256(raw).hexdigest() != pin:
    p.error('unreviewed UAPSD input')
s = raw.decode()
old = 'RELEASE_NDIS_PACKET(pAd, QUEUE_ENTRY_TO_PACKET(pEntry->pUAPSDEOSPFrame), NDIS_STATUS_FAILURE);'
count = 0
# Select reviewed early-return enqueue-failure releases; preserve other releases.
lines = s.splitlines(keepends=True)
for i, line in enumerate(lines):
    if old in line and (('pEntry->bAPSDFlagEOSPOK = 0;' in lines[i + 1]) or (not lines[i + 1].strip() and 'if (pAd->bAPSDFlagSPSuspend == 1)' in lines[i + 2])):
        indent = line[:len(line) - len(line.lstrip())]
        lines[i] = (indent + '/* Clear shared ownership before releasing rejected EOSP. */\n'
                    + indent + 'pEntry->pUAPSDEOSPFrame = NULL;\n'
                    + indent + 'RELEASE_NDIS_PACKET(pAd, pPkt, NDIS_STATUS_FAILURE);\n')
        count += 1
if count != 3:
    p.error('expected exactly three reviewed failure sites')
shutil.copytree(source, out)
(out / rel).write_text(''.join(lines), encoding='utf-8', newline='\n')
out.with_name(out.name + '-eosp-release.json').write_text(json.dumps({
    'input_sha256': {rel: pin},
    'output_sha256': {rel: hashlib.sha256((out / rel).read_bytes()).hexdigest()},
    'changed_failure_sites': count,
    'scope': 'EOSP ownership on enqueue failure only; callback lifetime/reuse unproved',
    'target_compiled': False, 'production_installed': False, 'runtime_verified': False
}, indent=2) + '\n', encoding='utf-8')
print('Staged three EOSP rejection ownership repairs; no production installation')
