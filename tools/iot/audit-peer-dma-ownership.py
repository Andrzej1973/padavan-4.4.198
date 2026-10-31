#!/usr/bin/env python3
"""Inventory packet-slot writes before adding completion identity metadata.

Lexical coverage includes inactive branches and RX; it is not an active callgraph.
Source text stays in local input; the report contains paths, lines and hashes only.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('source', type=Path)
p.add_argument('output', type=Path)
a = p.parse_args()
if a.output.exists():
    p.error('new report required')
pattern = re.compile(r'->\s*(pNdisPacket|pNextNdisPacket)\s*=(?!=)|\.\s*(pNdisPacket|pNextNdisPacket)\s*=(?!=)')
sites = []
files = {}
for path in sorted(a.source.rglob('*.c')):
    raw = path.read_bytes()
    # Vendor comments include non-UTF8 bytes in some translation units.
    text = raw.decode('utf-8', errors='replace')
    rel = path.relative_to(a.source).as_posix()
    for line, value in enumerate(text.splitlines(), 1):
        match = pattern.search(value)
        if match:
            files[rel] = hashlib.sha256(raw).hexdigest()
            rhs = value[match.end():].strip()
            sites.append({'file': rel, 'line': line,
                          'slot': match.group(1) or match.group(2),
                          'clears_slot': bool(re.match(r'NULL\s*;', rhs)),
                          'reviewed_for_identity': False})
report = {'scope': 'lexical DMA packet-slot write inventory; comments/inactive/RX included',
          'files_sha256': files, 'sites': sites,
          'active_target_coverage_proved': False,
          'identity_protocol_implemented': False,
          'constraints': ['two packet owners per descriptor',
                          'submission, cleanup, reset and DMA completion must clear/validate metadata',
                          'hardware TxS/FIFO completion identity is separate from DMA slot identity',
                          'never acquire MacTabLock under irq_lock without lock-order proof']}
a.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
print(f'Inventoried {len(sites)} packet-slot writes across {len(files)} files; active-target review required')
