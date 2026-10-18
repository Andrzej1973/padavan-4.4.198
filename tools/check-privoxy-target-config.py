#!/usr/bin/env python3
"""Parse copied image Privoxy seed configuration with its MIPS binary."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('romfs', type=Path)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    root = args.romfs.resolve()
    binary = root / 'usr/sbin/privoxy'
    seeds = root / 'usr/share/privoxy/privoxy'
    report = {'scope': 'QEMU MIPS seed-config parsing with temporary path rebasing; '
                       'daemon lifecycle, proxy traffic and device runtime unverified',
              'runtime_verified': False, 'checks': {}}
    try:
        qemu = shutil.which('qemu-mipsel-static') or shutil.which('qemu-mipsel')
        if not qemu:
            raise RuntimeError('Target QEMU is required')
        report['binary_sha256'] = hashlib.sha256(binary.read_bytes()).hexdigest()
        report['seed_config_sha256'] = hashlib.sha256((seeds / 'config').read_bytes()).hexdigest()
        with tempfile.TemporaryDirectory(prefix='privoxy-config-') as temporary:
            work = Path(temporary)
            for name in ('config', 'default.filter', 'user.filter', 'default.action',
                         'match-all.action', 'user.action', 'user.trust'):
                shutil.copyfile(seeds / name, work / name)
            shutil.copytree(root / 'usr/share/privoxy/templates', work / 'templates')
            text = (work / 'config').read_text()
            if len(re.findall(r'^confdir\s+', text, re.M)) != 1:
                raise RuntimeError('Expected one seed confdir directive')
            if re.search(r'^\s*logfile\s+', text, re.M):
                raise RuntimeError('Seed file logging must be disabled')
            text = text.replace('/etc/storage/privoxy', str(work))
            text = text.replace('/usr/share/privoxy/templates', str(work / 'templates'))
            text = re.sub(r'^logdir\s+.*$', 'logdir ' + str(work), text, flags=re.M)
            (work / 'config').write_text(text)
            result = subprocess.run(
                [qemu, '-L', str(root), str(binary), '--no-daemon', '--config-test',
                 str(work / 'config')], capture_output=True, timeout=30)
            report['config_test_exit'] = result.returncode
            report['checks']['mips_seed_config_accepted'] = result.returncode == 0
            # A malformed config must not be treated as accepted by a wrapper.
            (work / 'invalid').write_text('confdir ' + str(work) + '\n'
                                         'actionsfile missing-audit-actions-file\n')
            rejected = subprocess.run(
                [qemu, '-L', str(root), str(binary), '--no-daemon', '--config-test',
                 str(work / 'invalid')], capture_output=True, timeout=30)
            report['checks']['missing_actions_file_refused'] = rejected.returncode != 0
    except (OSError, RuntimeError, subprocess.TimeoutExpired) as error:
        report['error'] = str(error)
        report['checks']['inspection_completed'] = False
    report['success'] = bool(report['checks']) and all(report['checks'].values())
    args.report.write_text(json.dumps(report, indent=2) + '\n')
    if not report['success']:
        raise SystemExit('FAIL Privoxy target configuration parsing')
    print('PASS MIPS Privoxy seed config and invalid-config rejection; lifecycle unverified')


if __name__ == '__main__':
    main()
