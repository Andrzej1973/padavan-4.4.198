#!/usr/bin/env python3
"""Read compiler-emitted MIPS ELF32 ABI constants without executing code."""
import argparse
from pathlib import Path
import json
import struct
import hashlib

def read_layout(path, fields):
    data = path.read_bytes()
    if len(data) < 52 or data[:6] != b'\x7fELF\x01\x01':
        raise ValueError('Expected little-endian ELF32')
    if struct.unpack_from('<HH', data, 16) != (1, 8):
        raise ValueError('Expected relocatable MIPS object')
    offset = struct.unpack_from('<I', data, 32)[0]
    entry_size, count, names_index = struct.unpack_from('<HHH', data, 46)
    if entry_size != 40 or not count or names_index >= count or offset + count * 40 > len(data):
        raise ValueError('Invalid section table')
    sections = [struct.unpack_from('<10I', data, offset + n * 40) for n in range(count)]
    names = sections[names_index]
    if names[4] + names[5] > len(data):
        raise ValueError('Truncated section name table')
    strings = data[names[4]:names[4] + names[5]]
    matches = []
    for section in sections:
        index = section[0]
        if index >= len(strings):
            raise ValueError('Invalid section name offset')
        name = strings[index:].split(b'\0', 1)[0]
        if name == b'.bndabi':
            matches.append(section)
    if len(matches) != 1:
        raise ValueError('Expected unique .bndabi section')
    section = matches[0]
    if section[1] != 1 or section[5] != len(fields) * 4 or section[4] + section[5] > len(data):
        raise ValueError('Invalid ABI constant section')
    values = struct.unpack_from('<' + 'I' * len(fields), data, section[4])
    layout = dict(zip(fields, values))
    if layout['magic'] != 0x424e4441 or layout['pointer_size'] != 4 or layout['ulong_size'] != 4:
        raise ValueError('Unexpected ABI sentinel or target scalar width')
    return {'object_sha256': hashlib.sha256(data).hexdigest(), 'layout': layout}

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('directory', type=Path)
    a = p.parse_args()
    manifest = json.loads((a.directory / 'abi-probe-manifest.json').read_text(encoding='utf-8'))
    results = {radio: read_layout(a.directory / (radio + '-abi.o'), entry['fields'])
               for radio, entry in manifest['radios'].items()}
    output = {'target_compilation_verified': True, 'runtime_verified': False,
              'source_manifest': manifest, 'radios': results}
    (a.directory / 'abi-results.json').write_text(json.dumps(output, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(results, indent=2))
