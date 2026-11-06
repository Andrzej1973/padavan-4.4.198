#!/usr/bin/env python3
"""Inventory textual remap references without inferring runtime exclusion."""
import argparse
import hashlib
import json
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
for path in sorted(root.rglob('*.c')):
    # Vendor comments use mixed encodings; identifiers/register names are ASCII.
    lines = path.read_bytes().decode('latin-1').split('\n')
    hits = [{'line': n, 'text': line.strip()} for n, line in enumerate(lines, 1)
            if 'MCU_PCIE_REMAP_2' in line]
    if hits:
        relative = str(path.relative_to(root))
        files.append({'path': relative, 'sha256': actual[relative], 'references': hits})
result = {'scope': 'Textual C source references, including inactive guards/comments; aliases and numeric register accesses require separate audit',
          'hardware_serialization_proven': False, 'runtime_verified': False,
          'candidate_inventory_sha256': hashlib.sha256(json.dumps(actual, sort_keys=True).encode()).hexdigest(),
          'files': files}
a.output.write_text(json.dumps(result, indent=2) + '\n')
print(f'Inventoried {sum(len(f["references"]) for f in files)} references in {len(files)} files; no runtime claim')
