#!/usr/bin/env python3
"""Fail closed on Method1 ROM readiness timeout in the isolated candidate."""
import argparse
import hashlib
import json
from pathlib import Path


def patch(source):
    start = source.index('static NDIS_STATUS AndesMTLoadFwMethod1(')
    end = source.index('static NDIS_STATUS AndesMTLoadFwMethod2(', start)
    body = source[start:end]
    old = ('\tif (loop > 500) {\n'
           '\t\tDBGPRINT(RT_DEBUG_ERROR, ("%s: rom code is not ready(TOP_MISC2 = %d)\\n", __FUNCTION__, value));\n'
           '\t\tgoto done;\n\t}')
    if body.count(old) != 1:
        raise ValueError('Unexpected Method1 ROM timeout branch')
    new = old.replace('\t\tgoto done;',
                      '\t\tret = NDIS_STATUS_FAILURE;\n'
                      '\t\tCtl->Stage = FW_NO_INIT;\n'
                      '\t\tgoto done;')
    return source[:start] + body.replace(old, new) + source[end:]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('driver', type=Path)
    args = parser.parse_args()
    root = args.driver
    manifest_path = root.with_name(root.name + '.manifest.json')
    manifest = json.loads(manifest_path.read_text())
    actual = {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in root.rglob('*') if p.is_file()}
    if (manifest.get('production_installed') is not False or
            manifest.get('target_compiled') is not False or
            manifest.get('merged_driver_sha256') != actual):
        parser.error('Expected unchanged isolated candidate with full source inventory')
    relative = 'mcu/andes_mt.c'
    path = root / relative
    updated = patch(path.read_text())
    digest = hashlib.sha256(updated.encode()).hexdigest()
    manifest['firmware_rom_ready_timeout'] = {
        'input_sha256': actual[relative], 'output_sha256': digest,
        'scope': 'Method1 ROM timeout result only', 'epoch_verified': False}
    manifest['merged_driver_sha256'][relative] = digest
    manifest['candidate_driver_sha256'][relative] = digest
    path.write_text(updated)
    manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')


if __name__ == '__main__':
    main()
