#!/usr/bin/env python3
"""Check whether a pinned IoT candidate can overlay a prepared MT7603 tree.

This is a read-only source check. A conflict means the candidate would replace
another preparation's edits; it must be merged and reviewed before compilation.
"""

import argparse
import hashlib
import json
from pathlib import Path


SOURCE_DIRS = frozenset({'ap', 'common', 'hw_ctrl', 'include', 'mac', 'mcu', 'os', 'sniffer', 'tx_rx'})


def blob(data):
    return hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()


def check(manifest, candidate_root, prepared_root):
    originals = manifest.get('source_git_blobs')
    records = manifest.get('files')
    if not isinstance(originals, dict) or not isinstance(records, list):
        raise ValueError('Candidate manifest lacks source blobs or file records')
    if not originals or manifest.get('source_revision') != 'c25283e915a2a00a763774dd255b14aff997285e':
        raise ValueError('Candidate does not identify the pinned MT7603 source')
    overlays = {}
    for record in records:
        if not isinstance(record, dict) or not isinstance(record.get('path'), str) or not isinstance(record.get('sha256'), str):
            raise ValueError('Malformed candidate file record')
        name = record['path']
        if name.split('/', 1)[0] not in SOURCE_DIRS:
            continue
        if name in overlays or Path(name).is_absolute() or '..' in Path(name).parts:
            raise ValueError(f'Invalid candidate overlay path: {name}')
        candidate = candidate_root / name
        if not candidate.is_file() or hashlib.sha256(candidate.read_bytes()).hexdigest() != record['sha256']:
            raise ValueError(f'Candidate file absent or hash mismatch: {name}')
        overlays[name] = candidate
    if not overlays or not set(originals).issubset(overlays):
        raise ValueError('Candidate overlay does not cover its recorded original blobs')

    results = []
    for name in sorted(overlays):
        prepared = prepared_root / name
        if not prepared.is_file():
            state = 'missing_original' if name in originals else 'new_file_absent'
        elif name in originals:
            prepared_blob = blob(prepared.read_bytes())
            state = 'pristine_original' if prepared_blob == originals[name] else 'prepared_file_modified'
        else:
            state = 'same_new_file' if prepared.read_bytes() == overlays[name].read_bytes() else 'new_file_collision'
        results.append({'path': name, 'state': state})
    counts = {state: sum(item['state'] == state for item in results)
              for state in ('pristine_original', 'prepared_file_modified', 'missing_original',
                            'new_file_absent', 'same_new_file', 'new_file_collision')}
    return {'schema': 1, 'source_revision': manifest['source_revision'],
            'scope': 'candidate overlay against supplied prepared tree; source files only',
            'overlay_file_count': len(overlays), 'counts': counts, 'files': results,
            'safe_to_overlay_without_merge': counts['prepared_file_modified'] == 0
            and counts['missing_original'] == 0 and counts['new_file_collision'] == 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('candidate_manifest', type=Path)
    parser.add_argument('candidate_driver', type=Path)
    parser.add_argument('prepared_driver', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    for path in (args.candidate_manifest, args.candidate_driver, args.prepared_driver):
        if not path.exists():
            parser.error(f'Input is missing: {path}')
    if args.output and args.output.exists():
        parser.error('Output already exists; refusing to overwrite evidence')
    try:
        result = check(json.loads(args.candidate_manifest.read_text(encoding='utf-8')),
                       args.candidate_driver, args.prepared_driver)
    except ValueError as exc:
        parser.error(str(exc))
    rendered = json.dumps(result, indent=2) + '\n'
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding='utf-8')
    else:
        print(rendered, end='')
    if not result['safe_to_overlay_without_merge']:
        parser.exit(1, 'Prepared source conflicts with candidate; merge and review before target compile\n')


if __name__ == '__main__':
    main()
