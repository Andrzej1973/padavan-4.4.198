#!/usr/bin/env python3
"""Verify a downloaded source/toolchain archive against the committed registry."""
import hashlib
import json
import re
import sys
from pathlib import Path

root = Path(__file__).resolve().parent
if root.name == 'tools':
    root = root.parent
source_id, archive = sys.argv[1:]
registry = json.loads((root / 'sources.lock.json').read_text())
matches = [item for item in registry['sources'] if item['id'] == source_id]
if len(matches) != 1 or not re.fullmatch('[0-9a-f]{64}', matches[0].get('sha256') or ''):
    raise SystemExit('Missing or ambiguous pinned archive digest')
digest = hashlib.sha256()
with Path(archive).open('rb') as source:
    for chunk in iter(lambda: source.read(1024 * 1024), b''):
        digest.update(chunk)
if digest.hexdigest() != matches[0]['sha256']:
    raise SystemExit('Archive differs from pinned source registry: ' + source_id)
print('Verified {}: {}'.format(source_id, digest.hexdigest()))
