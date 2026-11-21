#!/usr/bin/env python3
"""Record native FT cache lifecycle constraints; PASS means source audit only."""
import argparse
import hashlib
import json
import re
from pathlib import Path

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('source', type=Path)
p.add_argument('--output', type=Path, required=True)
a = p.parse_args()
names = ('common/ft.c', 'ap/ap.c', 'common/cmm_cfg.c')
sources = {n: (a.source/n).read_text(encoding='latin1') for n in names}

def body(path, name):
    source = sources[path]
    # Mask strings and comments without moving offsets, then match balanced braces.
    masked = re.sub(r'/\*.*?\*/|//[^\n]*|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'',
                    lambda m: ' ' * len(m[0]), source, flags=re.S)
    match = re.search(r'\b' + re.escape(name) + r'\s*\([^;{}]*\)\s*\{', masked)
    if not match:
        raise ValueError('definition missing: ' + name)
    start = match.end() - 1
    depth = 1
    end = start + 1
    while depth and end < len(masked):
        depth += (masked[end] == '{') - (masked[end] == '}')
        end += 1
    if depth:
        raise ValueError('unbalanced definition: ' + name)
    return source[start:end]

ft = 'common/ft.c'
init = body(ft, 'FT_Init')
release = body(ft, 'FT_Release')
destroy = body(ft, 'FT_R1khEntryTabDestroy')
maintenance = body(ft, 'FT_R1KHInfoMaintenance')
radio = body('common/cmm_cfg.c', 'Set_RadioOn_Proc')
assert 'FT_RadioOff != TRUE' in init and 'FT_RadioOff != TRUE' in release
assert 'FT_Init(pAd);' in body('ap/ap.c', 'APStartUp')
for caller in ('APStop', 'APStopBssOnly'):
    assert 'FT_Release(pAd);' in body('ap/ap.c', caller)
assert destroy.index('FT_R1khEntryTabReady = FALSE') < destroy.index('RTMP_SEM_LOCK')
assert destroy.index('RTMP_SEM_UNLOCK') < destroy.index('NdisFreeSpinLock')
assert maintenance.index('FT_R1khEntryTabReady != TRUE') < maintenance.index('RTMP_SEM_LOCK')
lock = maintenance[maintenance.index('RTMP_SEM_LOCK'):maintenance.index('RTMP_SEM_UNLOCK')]
assert 'MacTableLookup(' in lock and 'MlmeEnqueue(' in lock
assert radio.index('MlmeRadioOff(pAd);') < radio.index('FT_RadioOff = TRUE')
assert radio.index('MlmeRadioOn(pAd);') < radio.index('FT_RadioOff = FALSE')
receipt = {
    'scope': 'native source lifecycle audit; not a concurrency or target test',
    'source_sha256': {n: hashlib.sha256((a.source/n).read_bytes()).hexdigest() for n in names},
    'constraints': [
        'APStopBssOnly reaches adapter-wide FT_Release; BSS-only admission cannot protect the shared cache lifetime',
        'FT_Init and FT_Release are conditional on FT_R1KH_KEEP and FT_RadioOff',
        'Set_RadioOn_Proc changes FT_RadioOff after the synchronous radio calls; callback ordering must be traced rather than inferred from final flag',
        'Destroy clears Ready before cache locking and frees the lock after unlocking',
        'Maintenance tests Ready before locking; that check alone does not retain cache lock lifetime',
        'Maintenance performs MacTableLookup and MlmeEnqueue while cache lock is held; introducing MacTabLock-to-cache nesting requires full reverse-order review'
    ],
    'required_before_install': 'adapter-lifetime admission for every cache caller and init/destroy, close/drain ordering, paired lock-order verification and target compilation',
    'producer_installed': False, 'runtime_verified': False
}
a.output.write_text(json.dumps(receipt, indent=2) + '\n')
print('PASS | FT cache lifecycle source audit | startup, full/BSS stop, radio flag ordering, destroy and maintenance constraints recorded')
