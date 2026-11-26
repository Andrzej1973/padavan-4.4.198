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


def check(image, romfs, zapret2=True, classic_only=False, without_sqm=False, with_sqm=False, vpn_protocols=(), without_eoip=False):
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
    if classic_only or without_sqm or without_eoip:
        listing = subprocess.check_output(
            ['unsquashfs', '-ls', '-offset', str(offsets[0]), str(image)],
            text=True).splitlines()
    if without_eoip:
        names = {'Advanced_Services_EoIP.asp', 'wr-eoip-status.js', 'wr-eoip-editor.js',
                 'wr-eoip-boot', 'eoip-service', 'eoip.ko', 'eoip.ko.gz', 'eoip.ko.xz'}
        for entry in listing:
            if Path(entry).name in names:
                raise ValueError('EoIP-excluded TRX contains EoIP: ' + entry)
    if without_sqm:
        for entry in listing:
            if (entry.endswith(('/Advanced_SQM.asp', '/sch_cake.ko')) or
                    entry == 'squashfs-root/usr/lib/sqm' or
                    entry.startswith('squashfs-root/usr/lib/sqm/')):
                raise ValueError('SQM-excluded TRX contains CAKE/SQM: ' + entry)
    if classic_only:
        paths = ['www/state.js']
        forbidden = ('squashfs-root/www/modern', 'squashfs-root/www/hybrid')
        if any(line == path or line.startswith(path + '/')
               for line in listing for path in forbidden):
            raise ValueError('Classic-only TRX contains Modern or Hybrid assets')
        iot_payloads = ('squashfs-root/www/Advanced_IoT_Content.asp',
                        'squashfs-root/www/classic-iot-config.js',
                        'squashfs-root/www/classic-iot-navigation.js',
                        'squashfs-root/usr/sbin/wr-classic-iot')
        if any(line == path or line.startswith(path + '/')
               for line in listing for path in iot_payloads):
            raise ValueError('Standard Classic TRX contains isolated IoT payload')
    # Verify the shared RC and Classic entry points against staged ROMFS.
    paths += ['bin/busybox', 'usr/sbin/httpd', 'sbin/rc', 'www/wr-band-status.js', 'www/index.asp',
              'www/Advanced_WAdvanced2g_Content.asp', 'www/Advanced_Services_Content.asp',
              *('www/' + language + '.dict' for language in ('EN', 'UK', 'RU'))]
    if zapret2:
        paths += ['www/Advanced_Services_Zapret2.asp', 'usr/sbin/nfqws2', 'usr/sbin/zapret2',
                  *('usr/share/zapret2/' + n for n in ('zapret-lib.lua', 'zapret-antidpi.lua', 'zapret-auto.lua')),
                  'usr/share/licenses/zapret2/LICENSE.txt']
    if with_sqm:
        manifest_path = Path(__file__).resolve().parents[1] / 'board-capabilities/wr1200js-cake.json'
        manifest = json.loads(manifest_path.read_text())
        paths += ['usr/lib/sqm/run.sh', 'www/' + manifest['classic_page']]
        for module in manifest['modules']:
            candidates = list((romfs / 'lib/modules').rglob(module))
            if len(candidates) != 1:
                raise ValueError('Expected one staged SQM module: ' + module)
            paths.append(candidates[0].relative_to(romfs).as_posix())
    if vpn_protocols:
        ip = romfs / 'bin/ip'
        if not ip.is_file() or not ip.stat().st_mode & 0o111:
            raise ValueError('Missing executable iproute2 fallback for VPN profiles')
        paths.append('bin/ip')
        paths += ['usr/sbin/wr-vpn-profile', 'usr/sbin/wr-vpn-profiles-service',
                  'usr/libexec/wrvpn/action-worker']
        for protocol in vpn_protocols:
            paths += ['usr/libexec/wrvpn/' + name for name in
                      (protocol, 'validate-' + protocol, 'readback-' + protocol)]
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
            if classic_only and name in ('usr/sbin/httpd', 'sbin/rc', 'www/state.js',
                                          'www/Advanced_WAdvanced2g_Content.asp'):
                markers=(b'Advanced_IoT_Content.asp',b'classic-iot-config.js',
                         b'classic-iot-navigation.js',b'wr_classic_iot',b'wr_iot_',b'br-iot')
                if any(marker in content for marker in markers):
                    raise ValueError('Standard Classic TRX contains isolated IoT control: ' + name)
            hashes[name] = hashlib.sha256(content).hexdigest()
            if name.startswith('www/modern/') and name.endswith(('.html', '.js', '.json')):
                references = sorted(set(re.findall(rb'[A-Za-z0-9_/-]+[.]asp', content)))
                if references:
                    modern_asp_references[name] = [value.decode('ascii') for value in references]
    return {'scope': 'Final image selected content equals verified ROMFS; no runtime acceptance',
            'image_sha256': hashlib.sha256(data).hexdigest(), 'squashfs_offset': offsets[0],
            'squashfs_created_epoch': int.from_bytes(data[offsets[0] + 8:offsets[0] + 12], 'little'),
            'files_sha256': hashes, 'classic_only_verified': classic_only,
            'iot_excluded_verified': classic_only,
            'sqm_excluded_verified': without_sqm, 'sqm_included_verified': with_sqm,
            'modern_asp_reference_literals': modern_asp_references,
            'eoip_excluded_verified': without_eoip, 'scratch_removed': True}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('image', type=Path)
    parser.add_argument('romfs', type=Path)
    parser.add_argument('--without-eoip', action='store_true')
    parser.add_argument('--without-zapret2', action='store_true')
    sqm = parser.add_mutually_exclusive_group()
    sqm.add_argument('--without-sqm', action='store_true')
    sqm.add_argument('--with-sqm', action='store_true')
    parser.add_argument('--vpn-protocol', action='append', choices=('wg', 'awg'), default=[])
    parser.add_argument('--classic-only', action='store_true')
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    result = check(args.image, args.romfs, not args.without_zapret2,
                   args.classic_only, args.without_sqm, args.with_sqm, args.vpn_protocol, args.without_eoip)
    args.report.write_text(json.dumps(result, indent=2) + '\n')
    print('PASS final TRX selected content/modes equal verified ROMFS; scratch removed; runtime unverified')
