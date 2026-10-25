#!/usr/bin/env python3
"""Assemble an isolated IoT MT7603 candidate with prepared source edits.

The output is a review candidate, not a production driver or compile result.
All inputs are read-only; the output directory must not exist.
"""

import argparse
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path


PINNED = 'c25283e915a2a00a763774dd255b14aff997285e'
SOURCE_DIRS = frozenset({'ap', 'common', 'hw_ctrl', 'include', 'mac', 'mcu', 'os', 'sniffer', 'tx_rx'})
EXPECTED_MODIFIED = frozenset({
    'ap/ap.c', 'ap/ap_cfg.c', 'common/rtmp_init.c',
    'hw_ctrl/cmm_asic_mt.c', 'include/rtmp.h',
})
CONFLICT = re.compile(rb'^<<<<<<< [^\n]*\n(.*?)^=======\n(.*?)^>>>>>>> [^\n]*\n', re.M | re.S)
RSSI_INIT = b'pAd->wr_rssi_birth = 0;\n\t\twr_rssi_kernel_init(&pAd->wr_rssi_observer);'
IOT_INIT = b'/* Last nonfailing initialization before adapter publication. */'
PUBLISH = b'*ppAdapter = (VOID *)pAd;'


def normalized(path):
    return path.read_bytes().replace(b'\r\n', b'\n')


def blob(data):
    return hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()


def merge(prepared, base, candidate, name):
    merge_input = prepared.with_name(prepared.name + '.iot-merge-input')
    if merge_input.exists():
        raise ValueError(f'Merge scratch path already exists: {merge_input}')
    merge_input.write_bytes(normalized(candidate))
    try:
        result = subprocess.run(['git', 'merge-file', '-p', '--', str(prepared), str(base),
                                 str(merge_input)], capture_output=True, check=False)
    finally:
        merge_input.unlink()
    if result.returncode not in (0, 1):
        raise ValueError(f'Merge command failed for {name}: {result.stderr.decode(errors="replace")}')
    data = result.stdout.replace(b'\r\n', b'\n')
    conflicts = list(CONFLICT.finditer(data))
    if name != 'common/rtmp_init.c':
        if result.returncode or conflicts or b'<<<<<<< ' in data:
            raise ValueError(f'Unexpected text conflict: {name}')
        return data, 0
    if result.returncode != 1 or len(conflicts) != 1 or data.count(b'<<<<<<< ') != 1:
        raise ValueError('Expected exactly one adapter initialization conflict')
    section = conflicts[0]
    ours, theirs = section.group(1).strip(), section.group(2).strip()
    if ours != RSSI_INIT or not theirs.startswith(IOT_INIT) or \
            b'wr_iot_ref_init' not in theirs or PUBLISH in theirs:
        raise ValueError('Adapter initialization conflict changed; manual review required')
    resolved = data[:section.start()] + section.group(1) + section.group(2) + data[section.end():]
    for marker in (RSSI_INIT, IOT_INIT, b'wr_iot_transition_lock', b'wr_iot_ref_init', PUBLISH):
        if resolved.count(marker) != 1:
            raise ValueError(f'Adapter initialization marker missing or duplicated: {marker!r}')
    if not (resolved.index(RSSI_INIT) < resolved.index(IOT_INIT) < resolved.index(PUBLISH)):
        raise ValueError('Adapter initialization must precede publication')
    return resolved, 1


def assemble(base_root, prepared_root, candidate_root, manifest, output):
    if output.exists():
        raise ValueError('Output already exists; refusing to overwrite files')
    if manifest.get('source_revision') != PINNED:
        raise ValueError('Candidate is not pinned to the reviewed source revision')
    originals = manifest.get('source_git_blobs')
    records = manifest.get('files')
    if not isinstance(originals, dict) or not isinstance(records, list):
        raise ValueError('Candidate manifest is incomplete')
    overlays = {}
    for item in records:
        if not isinstance(item, dict) or not isinstance(item.get('path'), str) or \
                not isinstance(item.get('sha256'), str):
            raise ValueError('Malformed candidate file record')
        name = item['path']
        if name.split('/', 1)[0] not in SOURCE_DIRS:
            continue
        if name in overlays or Path(name).is_absolute() or '..' in Path(name).parts:
            raise ValueError(f'Invalid candidate path: {name}')
        path = candidate_root / name
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != item['sha256']:
            raise ValueError(f'Candidate SHA-256 mismatch: {name}')
        overlays[name] = path
    # The original TIM admission probe uses 46/32. The later reviewed v39
    # lifecycle overlay uses 55/36; its corrected AP-client result ABI
    # includes the previously omitted ap_apcli.h prototype (56/37); its
    # WDS prototype and monitor implementation closure uses 58/39.
    if (len(overlays), len(originals)) not in ((46, 32), (55, 36), (56, 37), (58, 39)) or \
            not set(originals).issubset(overlays):
        raise ValueError('Candidate overlay shape changed; review required')
    for name, expected in originals.items():
        path = base_root / name
        if not path.is_file() or blob(path.read_bytes()) != expected:
            raise ValueError(f'Pinned upstream Git blob mismatch: {name}')

    modified = set()
    for name in overlays:
        prepared = prepared_root / name
        if name in originals:
            if not prepared.is_file():
                raise ValueError(f'Prepared original is absent: {name}')
            if blob(normalized(prepared)) != originals[name]:
                modified.add(name)
        elif prepared.exists():
            raise ValueError(f'Candidate new path collides with prepared source: {name}')
    if modified != EXPECTED_MODIFIED:
        raise ValueError(f'Prepared source overlap changed: {sorted(modified)}')

    shutil.copytree(prepared_root, output)
    merged = []
    for name, candidate in sorted(overlays.items()):
        destination = output / name
        if name in modified:
            # Normalize a scratch copy so Windows text writes do not create
            # whole-file conflicts that the Linux CI preparation would not.
            normalized_prepared = output / name
            normalized_prepared.write_bytes(normalized(prepared_root / name))
            data, conflict_count = merge(normalized_prepared, base_root / name,
                                         candidate, name)
            destination.write_bytes(data)
            merged.append({'path': name, 'resolved_text_conflicts': conflict_count})
        else:
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(normalized(candidate))
    result = {'schema': 1, 'source_revision': PINNED, 'overlay_count': len(overlays),
              'prepared_modified_paths': sorted(modified), 'merged_files': merged,
              'candidate_driver_sha256': {
                  name: hashlib.sha256((output / name).read_bytes()).hexdigest()
                  for name in sorted(overlays)},
              'target_compiled': False, 'production_installed': False,
              'runtime_verified': False}
    (output.parent / (output.name + '.manifest.json')).write_text(
        json.dumps(result, indent=2) + '\n', encoding='utf-8')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pinned_driver', type=Path)
    parser.add_argument('prepared_driver', type=Path)
    parser.add_argument('candidate_driver', type=Path)
    parser.add_argument('candidate_manifest', type=Path)
    parser.add_argument('output_driver', type=Path)
    args = parser.parse_args()
    if args.output_driver.exists():
        parser.error('Output already exists')
    try:
        manifest = json.loads(args.candidate_manifest.read_text(encoding='utf-8'))
        result = assemble(args.pinned_driver, args.prepared_driver,
                          args.candidate_driver, manifest, args.output_driver)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    print(f"Staged {result['overlay_count']} candidate paths with "
          f"{len(result['merged_files'])} prepared-source merges; target not compiled")


if __name__ == '__main__':
    main()
