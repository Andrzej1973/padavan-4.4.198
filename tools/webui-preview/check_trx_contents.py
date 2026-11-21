#!/usr/bin/env python3
"""Compare Modern/Zapret2 bytes in final SquashFS image with verified ROMFS; no runtime claim."""
import argparse
import hashlib
import json
import stat
import subprocess
import tempfile
from pathlib import Path


def check(image, romfs, zapret2=True):
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
    # Shared RC, Classic service/steering pages and dictionaries preserve the
    # existing management paths alongside Modern in this WR1200JS image.
    paths += ['usr/sbin/httpd', 'sbin/rc', 'www/wr-band-status.js',
              'www/Advanced_WAdvanced2g_Content.asp', 'www/Advanced_Services_Content.asp',
              *('www/' + language + '.dict' for language in ('EN', 'UK', 'RU'))]
    if zapret2:
        paths += ['usr/sbin/nfqws2', 'usr/sbin/zapret2',
                  *('usr/share/zapret2/' + n for n in ('zapret-lib.lua', 'zapret-antidpi.lua', 'zapret-auto.lua')),
                  'usr/share/licenses/zapret2/LICENSE.txt']
    hashes = {}
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
            hashes[name] = hashlib.sha256(content).hexdigest()
    return {'scope': 'Final image selected content equals verified ROMFS; no runtime acceptance',
            'image_sha256': hashlib.sha256(data).hexdigest(), 'squashfs_offset': offsets[0],
            'files_sha256': hashes, 'scratch_removed': True}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('image', type=Path)
    parser.add_argument('romfs', type=Path)
    parser.add_argument('--without-zapret2', action='store_true')
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    result = check(args.image, args.romfs, not args.without_zapret2)
    args.report.write_text(json.dumps(result, indent=2) + '\n')
    print('PASS final TRX selected content/modes equal verified ROMFS; scratch removed; runtime unverified')
