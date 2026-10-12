#!/usr/bin/env python3
"""Set reproducible project build identity in the pinned version file."""
import argparse
import re
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('source', type=Path)
p.add_argument('--number', required=True)
p.add_argument('--commit', required=True)
a = p.parse_args()
if not re.fullmatch(r'[1-9][0-9]{0,3}', a.number):
    p.error('build number must fit the RC four-digit version field')
if not re.fullmatch(r'[0-9a-f]{40}', a.commit):
    p.error('commit must be a full lowercase SHA')
path = a.source / 'trunk/versions.inc'
text = path.read_text(encoding='utf-8')
for key, old, new in (
    ('FIRMWARE_BUILDS_VER', '100', a.number),
    ('FIRMWARE_BUILDS_REV', 'shmily', a.commit[:8]),
):
    pattern = rf'^{key}={old}$'
    if len(re.findall(pattern, text, flags=re.M)) != 1:
        raise SystemExit('Pinned version anchor changed: ' + key)
    text = re.sub(pattern, key + '=' + new, text, flags=re.M)
path.write_text(text, encoding='utf-8')
print('Project test build identity: ' + a.number + '_' + a.commit[:8])
