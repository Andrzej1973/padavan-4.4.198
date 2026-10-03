#!/usr/bin/env python3
"""Derive the reduced MI-MINI profile; this does not port its kernel/board."""
import argparse
import re
from pathlib import Path

EXCLUDED = frozenset({
    'SMBD', 'WINS', 'SMBD_SYSLOG', 'TESTPARM', 'MINIDLNA',
    'TRANSMISSION', 'TRANSMISSION_WEB_CONTROL', 'ARIA', 'ARIA_WEB_CONTROL',
})
HEADER = '''### MI-MINI reduced profile for the Linux 4.4 port (port pending).
### File/storage/media services below are intentionally excluded:
### Samba/WINS and tools, miniDLNA, Transmission and Aria2 (including WebUIs).
### This router is not intended to serve as a NAS or download server.
### Commented selectors are documentation; future enabling needs build validation.
### This profile is not yet wired into the Linux 4.4 workflow.

'''


def prepare(source):
    lines = source.splitlines()
    values = {}
    positions = {}
    pattern = re.compile(r'^(#\s*)?(CONFIG_[A-Z0-9_]+)=(.*)$')
    for i, line in enumerate(lines):
        match = pattern.fullmatch(line)
        if not match:
            continue
        key = match.group(2)
        if key in positions:
            raise ValueError('Duplicate selector: ' + key)
        positions[key] = i
        values[key] = None if match.group(1) else match.group(3)
    identity = {
        'CONFIG_VENDOR': 'XIAOMI', 'CONFIG_PRODUCT': 'MT7620',
        'CONFIG_FIRMWARE_PRODUCT_ID': '"MI-MINI"',
    }
    for key, expected in identity.items():
        if values.get(key) != expected:
            raise ValueError('Unexpected MI-MINI identity: ' + key)
    for suffix in sorted(EXCLUDED):
        key = 'CONFIG_FIRMWARE_INCLUDE_' + suffix
        if key not in positions:
            raise ValueError('Missing documented selector: ' + key)
        lines[positions[key]] = '#' + key + '=y'
    # Other selections remain exactly as supplied. Dependency corrections belong
    # to the later 4.4 normalization step, after inspecting target recipes.
    return HEADER + '\n'.join(lines) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    if args.source.resolve() == args.output.resolve():
        parser.error('Keep the supplied source profile unchanged; use another output.')
    try:
        result = prepare(args.source.read_text(encoding='utf-8-sig'))
    except ValueError as exc:
        parser.error(str(exc))
    args.output.write_text(result, encoding='utf-8')
    print('Prepared MI-MINI reduced profile:', args.output)


if __name__ == '__main__':
    main()
