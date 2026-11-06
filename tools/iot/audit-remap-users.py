#!/usr/bin/env python3
"""Inventory textual remap references without inferring runtime exclusion."""
import argparse
import hashlib
import json
import re
from pathlib import Path

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('candidate', type=Path)
p.add_argument('output', type=Path)
a = p.parse_args()
root = a.candidate.resolve()
manifest = json.loads(Path(str(root) + '.manifest.json').read_text())
actual = {str(f.relative_to(root)): hashlib.sha256(f.read_bytes()).hexdigest()
          for f in root.rglob('*') if f.is_file()}
if actual != manifest['merged_driver_sha256']:
    p.error('Candidate differs from its recorded inventory')
files = []
header=(root/'include/mac/mac_mt/mt_mac.h').read_bytes().decode('latin-1')
base=re.search(r'^#define\s+MCU_CFG_BASE\s+(0x[0-9a-fA-F]+)\b',header,re.M)
offset=re.search(r'^#define\s+MCU_PCIE_REMAP_2\s+\(MCU_CFG_BASE\s*\+\s*(0x[0-9a-fA-F]+)\)',header,re.M)
if not base or not offset:
    p.error('Changed remap address definition; review aliases before inventory')
address=int(base[1],16)+int(offset[1],16)
literal=re.compile(r'\b0x0*'+format(address,'x')+r'\b',re.I)
for path in sorted(root.rglob('*.c')):
    # Vendor comments use mixed encodings; identifiers/register names are ASCII.
    lines = path.read_bytes().decode('latin-1').split('\n')
    hits = [{'line': n, 'text': line.strip()} for n, line in enumerate(lines, 1)
            if 'MCU_PCIE_REMAP_2' in line or literal.search(line)]
    if hits:
        relative = str(path.relative_to(root))
        files.append({'path': relative, 'sha256': actual[relative], 'references': hits})
result = {'scope': 'Textual C references by symbol or derived numeric address, including inactive guards/comments; other expressions and aliases require separate audit',
          'remap_address': hex(address),
          'hardware_serialization_proven': False, 'runtime_verified': False,
          'candidate_inventory_sha256': hashlib.sha256(json.dumps(actual, sort_keys=True).encode()).hexdigest(),
          'files': files}
a.output.write_text(json.dumps(result, indent=2) + '\n')
print(f'Inventoried {sum(len(f["references"]) for f in files)} references in {len(files)} files; no runtime claim')
