#!/usr/bin/env python3
"""Block close/removal while a WDS peer retirement reservation is retained."""
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
receipt = json.loads(src.with_name(src.name + '-slot-allocation.json').read_text())
if hashlib.sha256((src/'ap/ap_wds.c').read_bytes()).hexdigest() != receipt['output_sha256']:
    p.error('slot-allocation predecessor mismatch')
changes = {}
for name, variable, count in (
    ('interface-reference.h', 'r', 1),
    ('interface-registry.h', 'r', 2),
    ('aux-close-claim.h', 'record', 1),
):
    path = src/'include'/name
    text = path.read_text()
    old = f'if({variable}&&{variable}->peer_operation.active)return 0;'
    # Registry begin_remove has already validated r and uses a non-null spelling.
    bare = f'if({variable}->peer_operation.active)return 0;'
    found = text.count(old) + text.count(bare)
    if found != count:
        p.error(f'unreviewed guard layout: {name}: {found}')
    text = text.replace(old, f'if({variable}&&({variable}->peer_operation.active||{variable}->peer_operation.removing))return 0;')
    text = text.replace(bare, f'if({variable}->peer_operation.active||{variable}->peer_operation.removing)return 0;')
    changes[name] = text
shutil.copytree(src, out)
for name, text in changes.items():
    (out/'include'/name).write_text(text, encoding='utf-8', newline='\n')
out.with_name(out.name+'-retirement-close.json').write_text(json.dumps({
    'input_sha256': {n: hashlib.sha256((src/'include'/n).read_bytes()).hexdigest() for n in changes},
    'output_sha256': {n: hashlib.sha256((out/'include'/n).read_bytes()).hexdigest() for n in changes},
    'scope': 'close/release admission only; age-out reservation acquisition remains unbound',
    'target_compiled': False, 'production_installed': False,
}, indent=2)+'\n')
print('Staged WDS retirement close/removal/release exclusion')
