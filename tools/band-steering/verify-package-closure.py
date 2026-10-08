#!/usr/bin/env python3
"""Verify staged steering ELF files against the actual firmware runtime files."""
import argparse
import hashlib
import json
import os
import re
import struct
import subprocess
from pathlib import Path, PurePosixPath


def resolve_image(root, relative):
    """Follow every symlink component with absolute links rooted in the image."""
    pending = list(PurePosixPath(relative).parts)
    done = []
    links = 0
    while pending:
        part = pending.pop(0)
        if part in ('', '.', '/'):
            continue
        if part == '..':
            if not done:
                raise ValueError('Image path escapes root: ' + relative)
            done.pop()
            continue
        path = root.joinpath(*done, part)
        if path.is_symlink():
            links += 1
            if links > 32:
                raise ValueError('Image symlink loop: ' + relative)
            link = PurePosixPath(os.readlink(path))
            if link.is_absolute():
                done = []
            pending = list(link.parts) + pending
        else:
            done.append(part)
    path = root.joinpath(*done)
    if not path.is_file():
        raise ValueError('Missing image file: ' + relative)
    return path


def verify(staged, image, readelf, binaries=None):
    visited = {}
    environment = dict(os.environ, LC_ALL='C')

    def inspect(root, relative, kind):
        path = resolve_image(root, relative)
        name = kind + ':' + path.relative_to(root).as_posix()
        if name in visited:
            return
        data = path.read_bytes()
        if (len(data) < 52 or data[:7] != b'\x7fELF\x01\x01\x01' or
                struct.unpack_from('<H', data, 18)[0] != 8):
            raise ValueError('Expected little-endian ELF32 MIPS: ' + name)
        elf_type = struct.unpack_from('<H', data, 16)[0]
        if elf_type not in ((2, 3) if kind == 'candidate' else (3,)):
            raise ValueError('Unexpected executable/shared-library ELF type: ' + name)
        dynamic = subprocess.check_output([readelf, '-d', str(path)], text=True, env=environment)
        if re.search(r'\((?:RPATH|RUNPATH)\)', dynamic):
            raise ValueError('Unverified ELF runtime search path: ' + name)
        needed = re.findall(r'\(NEEDED\).*\[([^\]]+)\]', dynamic)
        visited[name] = {'sha256': hashlib.sha256(data).hexdigest(), 'needed': needed}
        for library in needed:
            if '/' in library or library in ('.', '..'):
                raise ValueError('Unsupported dependency name: ' + library)
            candidate = None
            for folder in ('lib', 'usr/lib'):
                relative_library = folder + '/' + library
                try:
                    resolve_image(image, relative_library)
                except ValueError as error:
                    if str(error).startswith('Missing image file:'):
                        continue
                    raise
                candidate = relative_library
                break
            if candidate is None:
                raise ValueError('Missing ' + library + ' required by ' + name)
            inspect(image, candidate, 'image')
        headers = subprocess.check_output([readelf, '-l', str(path)], text=True, env=environment)
        interpreter = re.search(r'Requesting program interpreter:\s*([^\]]+)\]', headers)
        if interpreter:
            loader = interpreter.group(1).strip()
            if not loader.startswith('/'):
                raise ValueError('Non-absolute interpreter: ' + name)
            inspect(image, loader.lstrip('/'), 'image')
        elif kind == 'candidate' and needed:
            raise ValueError('Dynamic executable has no interpreter: ' + name)

    if binaries is None:
        binaries = ('usr/sbin/wr-band-steering', 'usr/sbin/wr-band-steering-ctl')
    if not binaries:
        raise ValueError('No candidate executable selected')
    for binary in binaries:
        if binary.startswith('/') or '..' in binary.split('/'):
            raise ValueError('Candidate path must stay relative to staging root')
        inspect(staged, binary, 'candidate')
    return visited


def main():
    p = argparse.ArgumentParser()
    p.add_argument('staged', type=Path)
    p.add_argument('image', type=Path)
    p.add_argument('--readelf', default='readelf')
    p.add_argument('--binary', action='append', help='Relative staged executable; repeat for multiple seeds')
    p.add_argument('--production-image', action='store_true',
                   help='Candidates are files in the built normal ROMFS; runtime still unverified')
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    result = {'runtime_verified': False, 'production_installed': False,
              'dependency_closure_verified': False, 'elf_files': {}, 'errors': []}
    try:
        result['elf_files'] = verify(a.staged.resolve(), a.image.resolve(), a.readelf, a.binary)
        result['dependency_closure_verified'] = True
        result['production_installed'] = a.production_image
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        result['errors'].append(str(error))
    a.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
    return 1 if result['errors'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
