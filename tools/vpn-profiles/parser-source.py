#!/usr/bin/env python3
"""Extract verified VPN parser sources into a fresh test directory."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import tarfile

SOURCE_IDS = ('wireguard-tools-build-archive', 'amneziawg-tools-build-archive')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[2]
    lock = json.loads((repo / 'sources.lock.json').read_text(encoding='utf-8'))
    args.directory.mkdir()
    for label, source_id in zip(('wg', 'awg'), SOURCE_IDS):
        entry, = [item for item in lock['sources'] if item['id'] == source_id]
        archive = (repo / entry['repository_archive']).read_bytes()
        if hashlib.sha256(archive).hexdigest() != entry['sha256']:
            raise SystemExit('Parser archive checksum mismatch: ' + source_id)
        with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
            # Only regular src files are needed for the parser tests.
            for member in tar:
                parts = member.name.split('/')
                if not member.isfile() or len(parts) < 3 or parts[1] != 'src':
                    continue
                if any(part in ('', '.', '..') or '\\' in part or ':' in part for part in parts):
                    raise SystemExit('Invalid parser archive path')
                output = args.directory.joinpath(label, *parts[1:])
                output.parent.mkdir(parents=True, exist_ok=True)
                with output.open('xb') as stream:
                    stream.write(tar.extractfile(member).read())
        (args.directory / label / 'source-revision').write_text(entry['revision'] + '\n')


if __name__ == '__main__':
    main()
