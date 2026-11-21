#!/usr/bin/env python3
"""Record bounded generated HTTP library flags; never execute build metadata."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

LIMIT = 65536
PATTERNS = (
    'libnghttp*/nghttp*/build/CMakeCache.txt',
    'libnghttp*/nghttp*/build/lib/CMakeFiles/*/flags.make',
    'libnghttp*/nghttp*/build/lib/CMakeFiles/*/link.txt',
    'libngtcp2/ngtcp2*/build/CMakeCache.txt',
    'libngtcp2/ngtcp2*/build/lib/CMakeFiles/*/flags.make',
    'libngtcp2/ngtcp2*/build/lib/CMakeFiles/*/link.txt',
    'libcurl/curl-*/lib/Makefile', 'libcurl/curl-*/libtool',
)
CACHE_KEYS = re.compile(r'^(CMAKE_(C_FLAGS|CXX_FLAGS|C_COMPILER|CXX_COMPILER|AR|RANLIB|LINKER|BUILD_TYPE|SYSROOT|SHARED_LINKER_FLAGS)|BUILD_|ENABLE_)')
MAKE_KEYS = re.compile(r'^(AM_CFLAGS|AM_CPPFLAGS|CFLAGS|CPPFLAGS|LDFLAGS|LIBS|libcurl_la_LDFLAGS|libcurl_la_LIBADD|NGHTTP\w*|NGTCP\w*)\s*=')
TOOL_KEYS = re.compile(r'^(archive_cmds|archive_expsym_cmds|exclude_expsyms|export_dynamic_flag_spec|whole_archive_flag_spec|with_gnu_ld|version_type|compiler|wl)=')

def collect(tree):
    base = (tree / 'trunk/libs').resolve()
    records = {}
    if not base.is_dir():
        return {'scope': 'Generated compile/link metadata only; not build/runtime acceptance', 'state': 'library tree missing', 'files': records}
    paths = sorted({p for pattern in PATTERNS for p in base.glob(pattern)})
    if len(paths) > 64:
        raise ValueError('Unexpected number of provenance files')
    for path in paths:
        if path.is_symlink() or not path.resolve().is_relative_to(base):
            continue
        if not path.is_file():
            continue
        # Metadata caps avoid copying large logs, caches or arbitrary source trees.
        with path.open('rb') as stream:
            raw = stream.read(LIMIT + 1)
        clipped = len(raw) > LIMIT
        raw = raw[:LIMIT]
        lines = raw.decode('utf-8', errors='replace').splitlines()
        if path.name == 'CMakeCache.txt':
            lines = [line for line in lines if CACHE_KEYS.match(line)]
        elif path.name in ('Makefile', 'libtool'):
            matcher = MAKE_KEYS if path.name == 'Makefile' else TOOL_KEYS
            selected, continuation = [], False
            for line in lines:
                if matcher.match(line) or continuation:
                    selected.append(line)
                    continuation = line.rstrip().endswith('\\')
            lines = selected
        records[str(path.relative_to(base))] = {'sample_sha256': hashlib.sha256(raw).hexdigest(),
                'sample_truncated': clipped, 'selected_lines': lines}
    return {'scope': 'Generated compile/link metadata only; not build/runtime acceptance', 'state': 'collected', 'files': records}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('tree', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = collect(args.tree)
    report['tools'] = {}
    for tool in ('cmake', 'libtoolize', 'pkg-config', 'autoconf'):
        try:
            result = subprocess.run([tool, '--version'], capture_output=True, text=True, timeout=5)
            report['tools'][tool] = {'code': result.returncode, 'version': result.stdout.splitlines()[:1]}
        except (OSError, subprocess.TimeoutExpired) as exc:
            report['tools'][tool] = {'error': type(exc).__name__}
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print('HTTP library provenance files:', len(report['files']))

if __name__ == '__main__':
    main()
