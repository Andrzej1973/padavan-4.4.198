#!/usr/bin/env python3
"""Select explicitly supported firmware recipes; pending boards never enter CI."""
import json
import os
import sys
from pathlib import Path

catalog = json.loads(Path('boards.json').read_text())['boards']
ids = [board['id'] for board in catalog]
if len(ids) != len(set(ids)):
    raise SystemExit('Duplicate board IDs')
for board in catalog:
    config = Path(board['config'])
    if not config.is_file() or config.is_absolute() or '..' in config.parts:
        raise SystemExit('Invalid board configuration path')
selection = sys.argv[1] if len(sys.argv) > 1 else 'all-supported'
requested = ids if selection == 'all-supported' else selection.split(',')
unknown = set(requested) - set(ids)
if unknown:
    raise SystemExit('Unknown boards: ' + ','.join(sorted(unknown)))
selected = [board for board in catalog if board['id'] in requested and board['build_enabled']]
if selection != 'all-supported' and len(selected) != len(set(requested)):
    raise SystemExit('Requested board port is not enabled for firmware builds')
if not selected:
    raise SystemExit('No supported boards selected')
if any(board['recipe'] != 'wr1200js' for board in selected):
    raise SystemExit('No verified reusable recipe registered for selected board')
matrix = {'include': [{'board': board['id']} for board in selected]}
value = json.dumps(matrix, separators=(',', ':'))
print(value)
if os.environ.get('GITHUB_OUTPUT'):
    with open(os.environ['GITHUB_OUTPUT'], 'a') as output:
        output.write('matrix=' + value + '\n')
Path('selected-boards.json').write_text(json.dumps(selected, indent=2) + '\n')
