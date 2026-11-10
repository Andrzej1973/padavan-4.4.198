#!/usr/bin/env python3
"""Check prepared Modern assets and route literals in the built ROMFS (not device acceptance)."""
import argparse
import hashlib
import json
from pathlib import Path


def check(source):
    trunk = source / 'trunk'
    prepared = trunk / 'user/www/modern'
    installed = trunk / 'romfs/www/modern'
    names = ('index.html', 'app.js', 'wifi.js', 'shared-wifi.js',
             'wifi-schema.json', 'styles.css', 'favicon.svg')
    hashes = {}
    for name in names:
        expected = (prepared / name).read_bytes()
        actual = (installed / name).read_bytes()
        if actual != expected:
            raise ValueError('Modern ROMFS asset differs: ' + name)
        hashes[name] = hashlib.sha256(actual).hexdigest()
    schema = json.loads((installed / 'wifi-schema.json').read_text())
    if schema.get('demo') is not False:
        raise ValueError('DEMO Wi-Fi schema in production image')
    destinations = sorted({page['classic'] for band in schema['pages'].values() for page in band.values()})
    for destination in destinations:
        if Path(destination).name != destination or not destination.endswith('.asp'):
            raise ValueError('Invalid Classic destination: ' + destination)
        if not (trunk / 'romfs/www' / destination).is_file():
            raise ValueError('Missing Classic destination in ROMFS: ' + destination)
    httpd = (trunk / 'romfs/usr/sbin/httpd').read_bytes()
    for route in ['wr_modern.json', *('modern/' + n for n in names)]:
        if route.encode() + b'\0' not in httpd:
            raise ValueError('Missing compiled Modern route literal: ' + route)
    return {'scope': 'ROMFS assets and compiled route literals, not runtime/authentication proof',
            'classic_destinations': destinations, 'assets_sha256': hashes, 'httpd_sha256': hashlib.sha256(httpd).hexdigest()}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    report = check(args.source)
    if args.report:
        args.report.write_text(json.dumps(report, indent=2) + '\n')
    print('PASS Modern ROMFS assets match prepared source; compiled route literals present; runtime unverified')
