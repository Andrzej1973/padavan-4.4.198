#!/usr/bin/env python3
"""Verify selected firmware files and the Classic-only policy in final SquashFS."""
import argparse
import hashlib
import json
import re
import stat
import subprocess
import tempfile
from pathlib import Path


def check(image, romfs, zapret2=True, classic_only=False):
    data = image.read_bytes()
    # Padavan appends SquashFS to its kernel image; validate candidates with unsquashfs.
    offsets = []
    start = 0
    while True:
        offset = data.find(b'hsqs', start)
        if offset < 0:
            break
        start = offset + 4
        result = subprocess.run(['unsquashfs', '-s', '-offset', str(offset), str(image)],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if result.returncode == 0:
            offsets.append(offset)
    if len(offsets) != 1:
        raise ValueError('Expected one valid embedded SquashFS, found ' + str(len(offsets)))
    paths = ['www/modern/' + name for name in (
        'index.html', 'app.js', 'wifi.js', 'shared-wifi.js', 'wifi-schema.json', 'styles.css', 'favicon.svg')]
    if classic_only:
        paths = ['www/state.js']
        listing = subprocess.check_output(
            ['unsquashfs', '-ls', '-offset', str(offsets[0]), str(image)],
            text=True)
        forbidden = ('squashfs-root/www/modern', 'squashfs-root/www/hybrid')
        if any(line == path or line.startswith(path + '/')
               for line in listing.splitlines() for path in forbidden):
            raise ValueError('Classic-only TRX contains Modern or Hybrid assets')
    # Verify the shared RC and Classic entry points against staged ROMFS.
    paths += ['usr/sbin/httpd', 'sbin/rc', 'www/wr-band-status.js', 'www/index.asp',
              'www/Advanced_WAdvanced2g_Content.asp', 'www/Advanced_Services_Content.asp',
              *('www/' + language + '.dict' for language in ('EN', 'UK', 'RU'))]
    if zapret2:
        paths += ['usr/sbin/nfqws2', 'usr/sbin/zapret2',
                  *('usr/share/zapret2/' + n for n in ('zapret-lib.lua', 'zapret-antidpi.lua', 'zapret-auto.lua')),
                  'usr/share/licenses/zapret2/LICENSE.txt']
    hashes = {}
    modern_asp_references = {}
    with tempfile.TemporaryDirectory(prefix='wr-trx-content-') as scratch:
        extracted = Path(scratch) / 'root'
        subprocess.run(['unsquashfs', '-no-progress', '-processors', '1', '-offset', str(offsets[0]),
                        '-dest', str(extracted), str(image), *paths], check=True, stdout=subprocess.DEVNULL)
        for name in paths:
            expected, actual = romfs / name, extracted / name
            if not stat.S_ISREG(expected.lstat().st_mode) or not stat.S_ISREG(actual.lstat().st_mode):
                raise ValueError('Expected regular file: ' + name)
            content = actual.read_bytes()
            if content != expected.read_bytes():
                raise ValueError('TRX differs from verified ROMFS: ' + name)
            if stat.S_IMODE(actual.stat().st_mode) != stat.S_IMODE(expected.stat().st_mode):
                raise ValueError('TRX mode differs from verified ROMFS: ' + name)
            if classic_only and name in ('usr/sbin/httpd', 'www/state.js', 'www/index.asp'):
                if any(marker in content for marker in
                       (b'wr_modern.json', b'modern/index.html', b'hybrid/index.html')):
                    raise ValueError('Classic-only TRX contains a Modern/Hybrid route: ' + name)
            hashes[name] = hashlib.sha256(content).hexdigest()
            if name.startswith('www/modern/') and name.endswith(('.html', '.js', '.json')):
                references = sorted(set(re.findall(rb'[A-Za-z0-9_/-]+[.]asp', content)))
                if references:
                    modern_asp_references[name] = [value.decode('ascii') for value in references]
    return {'scope': 'Final image selected content equals verified ROMFS; no runtime acceptance',
            'image_sha256': hashlib.sha256(data).hexdigest(), 'squashfs_offset': offsets[0],
            'files_sha256': hashes, 'classic_only_verified': classic_only,
            'modern_asp_reference_literals': modern_asp_references,
            'scratch_removed': True}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('image', type=Path)
    parser.add_argument('romfs', type=Path)
    parser.add_argument('--without-zapret2', action='store_true')
    parser.add_argument('--classic-only', action='store_true')
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    result = check(args.image, args.romfs, not args.without_zapret2, args.classic_only)
    args.report.write_text(json.dumps(result, indent=2) + '\n')
    print('PASS final TRX selected content/modes equal verified ROMFS; scratch removed; runtime unverified')
