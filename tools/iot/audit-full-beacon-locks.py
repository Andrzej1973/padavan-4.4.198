#!/usr/bin/env python3
"""Inventory beacon locks in a pinned MT7603 tree with a partial candidate overlay.

This is source-text evidence only. It does not infer target preprocessing,
compilation, call context, or runtime behavior.
"""

import argparse
import hashlib
import json
import re
from pathlib import Path


SOURCE_DIRS = frozenset({'ap', 'common', 'hw_ctrl', 'include', 'mac', 'mcu', 'os', 'tx_rx'})
FUNCTION = re.compile(
    r'^\s*(?:(?:static|inline|extern)\s+)*'
    r'(?:VOID|INT|INT16|INT32|INT64|BOOLEAN|NDIS_STATUS|UCHAR|UINT|'
    r'UINT16|UINT32|UINT64|LONG|ULONG|void|int|bool)\s+([A-Za-z_]\w*)\s*\('
)
LOCK = re.compile(r'RTMP_(SEM|IRQ)_LOCK\s*\(\s*&pAd->BcnRingLock')
FULL_CANDIDATE_SHAPE = (515, 45, 31, 9, 20, 11, 9)


def git_blob(data):
    return hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()


def files_under(root):
    return {p.relative_to(root).as_posix(): p for p in root.rglob('*') if p.is_file()}


def inventory(source, candidate, manifest):
    if manifest.get('source_revision') != 'c25283e915a2a00a763774dd255b14aff997285e':
        raise ValueError('Candidate source revision is not the pinned MT7603 revision')
    originals = manifest.get('source_git_blobs')
    if not isinstance(originals, dict) or not originals:
        raise ValueError('Candidate has no original Git blob inventory')

    source_files = files_under(source)
    candidate_files = {
        name: path for name, path in files_under(candidate).items()
        if name.split('/', 1)[0] in SOURCE_DIRS
    }
    for name, expected in originals.items():
        path = source_files.get(name)
        if path is None or git_blob(path.read_bytes()) != expected:
            raise ValueError(f'Pinned source Git blob mismatch: {name}')
    for name in candidate_files:
        if name in source_files and name not in originals:
            raise ValueError(f'Overlaid original has no recorded Git blob: {name}')
        if name in originals and name not in source_files:
            raise ValueError(f'Overlaid source is absent from pinned tree: {name}')

    sites = []
    paths = {name for name in source_files | candidate_files if name.endswith('.c')}
    for name in sorted(paths):
        path = candidate_files.get(name, source_files.get(name))
        owner = None
        for number, line in enumerate(path.read_text(encoding='utf-8', errors='replace').splitlines(), 1):
            if line.lstrip().startswith(('/', '*')):
                continue
            declaration = FUNCTION.match(line)
            if declaration:
                owner = declaration.group(1)
            match = LOCK.search(line)
            if match:
                if owner is None:
                    raise ValueError(f'Beacon lock has no function owner: {name}:{number}')
                sites.append({
                    'file': name, 'line': number, 'function': owner,
                    'form': match.group(1), 'candidate_overlay': name in candidate_files,
                    'active_after_directives': None,
                })

    return {
        'schema': 1,
        'scope': 'full pinned MT7603 source plus partial candidate overlay; source-text only',
        'source_revision': manifest['source_revision'],
        'source_file_count': len(source_files),
        'candidate_overlay_file_count': len(candidate_files),
        'original_git_blobs_verified': len(originals),
        'assembled_file_count': len(source_files.keys() | candidate_files.keys()),
        'lock_units': len({site['file'] for site in sites}),
        'lock_sites': len(sites),
        'forms': {form: sum(site['form'] == form for site in sites)
                  for form in ('SEM', 'IRQ')},
        'sites': sites,
        'target_compiled': False,
        'production_installed': False,
        'runtime_verified': False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pinned_source', type=Path)
    parser.add_argument('candidate_driver', type=Path)
    parser.add_argument('candidate_manifest', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--expect-full-candidate', action='store_true',
                        help='require the reviewed pinned-source and overlay inventory')
    args = parser.parse_args()
    if args.output.exists():
        parser.error('Output already exists; refusing to overwrite evidence')
    for root in (args.pinned_source, args.candidate_driver):
        if not root.is_dir():
            parser.error(f'Input directory is missing: {root}')
    manifest = json.loads(args.candidate_manifest.read_text(encoding='utf-8'))
    result = inventory(args.pinned_source, args.candidate_driver, manifest)
    if args.expect_full_candidate:
        shape = (result['source_file_count'], result['candidate_overlay_file_count'],
                 result['original_git_blobs_verified'], result['lock_units'],
                 result['lock_sites'], result['forms']['SEM'], result['forms']['IRQ'])
        if shape != FULL_CANDIDATE_SHAPE:
            parser.error(f'Candidate coverage changed: {shape}; expected '
                         f'{FULL_CANDIDATE_SHAPE}. Review the candidate before updating this gate.')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(f"Verified {result['original_git_blobs_verified']} source blobs; "
          f"found {result['lock_sites']} lock sites in {result['lock_units']} units")


if __name__ == '__main__':
    main()
