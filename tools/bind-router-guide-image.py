#!/usr/bin/env python3
"""Bind generated model guides to the final packaged firmware image."""
import argparse
import hashlib
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('image', type=Path)
    parser.add_argument('guides', type=Path, nargs='+')
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    if not args.image.is_file() or args.image.stat().st_size == 0:
        raise SystemExit('Missing or empty firmware image')
    digest = hashlib.sha256()
    with args.image.open('rb') as image:
        for chunk in iter(lambda: image.read(1024 * 1024), b''):
            digest.update(chunk)
    marker = 'Ідентичність готового образу'
    block = (marker + '\n'
             + 'Файл: ' + args.image.name + '\n'
             + 'SHA-256: ' + digest.hexdigest() + '\n')
    # Validate every input before modifying any guide. Refuse stale bindings;
    # never silently carry an earlier image identity into a new package.
    pending = []
    for path in args.guides:
        text = path.read_text(encoding='utf-8')
        if marker in text:
            if text.count(marker) != 1 or text.split(marker, 1)[1] != block[len(marker):]:
                raise SystemExit('Stale or malformed image identity: ' + str(path))
        elif args.check:
            raise SystemExit('Missing image identity: ' + str(path))
        else:
            pending.append((path, text.rstrip() + '\n\n' + block))
    for path, text in pending:
        path.write_text(text, encoding='utf-8')
    print('PASS final firmware name and SHA-256 bound to model guides')


if __name__ == '__main__':
    main()
