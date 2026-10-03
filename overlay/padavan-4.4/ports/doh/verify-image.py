#!/usr/bin/env python3
"""Verify DoH image packaging and target ELF closure; runtime remains unverified."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('trunk', type=Path)
parser.add_argument('report', type=Path)
args = parser.parse_args()
root = args.trunk.resolve() / 'romfs'
checks, details = {}, {}


def target(name):
    parts = list(Path(name.lstrip('/')).parts)
    current, hops = root, 0
    while parts:
        part = parts.pop(0)
        current = current.parent if part == '..' else current / part
        if current != root and root not in current.parents:
            raise RuntimeError('ROMFS path escaped root')
        if current.is_symlink():
            hops += 1
            if hops > 40:
                raise RuntimeError('ROMFS symlink loop')
            link = os.readlink(current)
            current = root if link.startswith('/') else current.parent
            parts = list(Path(link.lstrip('/')).parts) + parts
    return current


def mips(path):
    data = path.read_bytes()[:20]
    return len(data) == 20 and data[:4] == b'\x7fELF' and data[4:6] == b'\x01\x01' and int.from_bytes(data[18:20], 'little') == 8


try:
    checks['selector'] = 'CONFIG_FIRMWARE_INCLUDE_DOH=y' in (args.trunk / '.config').read_text().splitlines()
    binary = target('/usr/sbin/https_dns_proxy')
    checks['binary'] = mips(binary) and bool(binary.stat().st_mode & 0o111)
    helper_path = target('/usr/bin/doh_proxy.sh')
    helper = helper_path.read_text()
    checks['lifecycle'] = bool(helper_path.stat().st_mode & 0o111) and all(x in helper for x in ('flock -x -n 9', 'owned_pid', '-C "$ca"', '9>&-', '65532'))
    checks['helper_syntax'] = subprocess.run(['sh', '-n', str(helper_path)]).returncode == 0
    checks['ca_bundle'] = hashlib.sha256(target('/usr/share/doh-proxy/cacert.pem').read_bytes()).hexdigest() == 'a41b5d356aea97a529fe27e0f7316d2f9d946d75927476cf9cf1b90637d00505'
    checks['license'] = 'Copyright (c) 2016 Aaron Drew' in target('/usr/share/doh-proxy/LICENSE').read_text()
    page = target('/www/Advanced_Services_DoH.asp').read_text()
    keys = ['doh_enable', 'doh_server0', 'doh_server1', 'doh_server2', 'doh_server3', 'doh_quic', 'doh_bootstrap_dns', 'doh_listen_port', 'doh_listen_mode', 'doh_mode']
    checks['webui'] = all(key in page for key in keys) and 'login_safe()' in page and 'found_app_doh()' in page
    catalogue = json.loads(target('/www/doh.json').read_text())
    checks['resolver_catalogue'] = isinstance(catalogue, list) and bool(catalogue) and all(isinstance(item.get('name'), str) and item.get('url', '').startswith('https://') for item in catalogue)
    rc = target('/sbin/rc').read_bytes()
    httpd = target('/usr/sbin/httpd').read_bytes()
    checks['rc'] = b'/usr/bin/doh_proxy.sh' in rc and b'restart_doh' in rc
    checks['backend'] = b'found_app_doh' in httpd and b'doh_value' in httpd and all(key.encode() in httpd for key in keys)
    queue, visited, missing, invalid_elf = [binary], set(), [], []
    while queue:
        path = queue.pop()
        if path in visited:
            continue
        visited.add(path)
        if not mips(path):
            invalid_elf.append(str(path.relative_to(root)))
        needed = re.findall(r'\(NEEDED\).*\[([^\]]+)\]', subprocess.check_output(['readelf', '-d', str(path)], text=True))
        for name in needed:
            dependency = next((p for p in (target('/lib/' + name), target('/usr/lib/' + name)) if p.is_file()), None)
            if dependency is None:
                missing.append(name)
            else:
                queue.append(dependency)
    checks['shared_libraries'] = not missing and not invalid_elf
    details.update(missing_libraries=sorted(set(missing)), invalid_elf=invalid_elf,
                   inspected_elf_files=sorted(str(p.relative_to(root)) for p in visited))
    interpreters = re.findall(r'Requesting program interpreter:\s*([^\]]+)', subprocess.check_output(['readelf', '-l', str(binary)], text=True))
    checks['loader'] = len(interpreters) == 1 and target(interpreters[0]).is_file() and mips(target(interpreters[0]))
    defaults = (args.trunk / 'user/shared/defaults.c').read_text()
    checks['default_disabled'] = '{ "doh_enable", "0" }' in defaults
except (OSError, RuntimeError, ValueError, subprocess.CalledProcessError) as error:
    checks['inspection_completed'] = False
    details['error'] = str(error)
args.report.write_text(json.dumps({'scope': 'DoH packaging/configuration/ELF; browser, DNS, TLS and runtime unverified', 'checks': checks, 'details': details}, indent=2) + '\n')
if not all(checks.values()):
    raise SystemExit('DoH image check failed: ' + ', '.join(name for name, value in checks.items() if not value))
print('DoH image/ELF checks passed; runtime remains unverified')
