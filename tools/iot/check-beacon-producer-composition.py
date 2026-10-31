#!/usr/bin/env python3
"""Verify an isolated beacon-gate tree against its complete parent and delta."""
import argparse
import hashlib
import json
from pathlib import Path


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inventory(root):
    return {p.relative_to(root).as_posix(): digest(p)
            for p in root.rglob('*') if p.is_file()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('parent', type=Path)
    parser.add_argument('parent_manifest', type=Path)
    parser.add_argument('candidate', type=Path)
    parser.add_argument('delta_manifest', type=Path)
    args = parser.parse_args()
    parent = inventory(args.parent)
    candidate = inventory(args.candidate)
    parent_report = json.loads(args.parent_manifest.read_text(encoding='utf-8'))
    delta = json.loads(args.delta_manifest.read_text(encoding='utf-8'))
    recorded_parent = {row['path']: row['sha256'] for row in parent_report['files']}
    changes = delta['candidate_files']
    if parent_report.get('production_installed') is not False or parent != recorded_parent:
        parser.error('parent inventory/hash or nonproduction provenance differs')
    if delta.get('production_installed') is not False or delta.get('target_compiled') is not False:
        parser.error('delta has unexpected production/compile claim')
    if not changes or not set(changes).issubset(candidate):
        parser.error('delta inventory is empty or names missing output files')
    if set(candidate) != set(parent) | set(changes):
        parser.error('candidate inventory differs from parent plus declared additions')
    for name, value in candidate.items():
        expected = changes[name] if name in changes else parent[name]
        if value != expected:
            parser.error('candidate hash differs: ' + name)
    if {name for name in candidate if parent.get(name) != candidate[name]} != set(changes):
        parser.error('delta is not the exact set of changed/added files')
    print('PASS isolated beacon candidate: parent', len(parent), 'delta',
          len(changes), 'complete output', len(candidate), 'hashes')


if __name__ == '__main__':
    main()
