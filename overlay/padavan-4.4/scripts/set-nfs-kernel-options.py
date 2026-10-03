#!/usr/bin/env python3
"""Map optional firmware NFS selectors to a board kernel template before configure."""
import argparse
from pathlib import Path
import re

parser = argparse.ArgumentParser()
parser.add_argument('firmware_config', type=Path)
parser.add_argument('kernel_template', type=Path)
parser.add_argument('--verify', action='store_true', help='Check effective config without modifying it')
args = parser.parse_args()
requested = args.firmware_config.read_text(encoding='utf-8').splitlines()

def selected(name):
    active = [line.strip().split('=', 1)[1] for line in requested
              if re.match(r'^' + re.escape(name) + r'=', line.strip())]
    if len(active) > 1 or (active and active[0] not in ('y', 'n')):
        raise SystemExit('Invalid or duplicate selector: ' + name)
    return active == ['y']

client = selected('CONFIG_FIRMWARE_INCLUDE_NFSC')
server = selected('CONFIG_FIRMWARE_INCLUDE_NFSD')
options = {
    'CONFIG_NFS_FS': client,
    'CONFIG_NFS_V2': client,
    'CONFIG_NFS_V3': client,
    'CONFIG_NFS_V3_ACL': client,
    'CONFIG_NFSD': server,
    'CONFIG_NFSD_V2_ACL': server,
    'CONFIG_NFSD_V3': server,
    'CONFIG_NFSD_V3_ACL': server,
}
lines = args.kernel_template.read_text(encoding='utf-8').splitlines()
if args.verify:
    failures = []
    for name, expected in options.items():
        values = [line.split('=', 1)[1] for line in lines if line.startswith(name + '=')]
        actual = values[0] if len(values) == 1 else 'n' if not values else 'duplicate'
        if (expected and actual != 'y') or (not expected and actual not in ('n',)):
            failures.append('%s: expected %s, got %s' % (name, 'y' if expected else 'n', actual))
    if failures:
        raise SystemExit('\n'.join(failures))
    print('Effective kernel NFS options match the firmware selectors')
    raise SystemExit(0)
# Validate every expected anchor before changing the template. Keep shared RPC,
# lock manager and other filesystem choices for Kconfig to resolve normally.
for name in options:
    matches = [i for i, line in enumerate(lines)
               if re.fullmatch(re.escape(name) + r'=[ymn]', line)
               or line == '# ' + name + ' is not set']
    if len(matches) != 1:
        raise SystemExit('Inspect kernel template symbol: ' + name)
    lines[matches[0]] = name + '=y' if options[name] else '# ' + name + ' is not set'
if client or server:
    if 'CONFIG_NETWORK_FILESYSTEMS=y' not in lines:
        raise SystemExit('NFS requires NETWORK_FILESYSTEMS in the board template')
args.kernel_template.write_text('\n'.join(lines) + '\n', encoding='utf-8')
print('NFS template: client=%s server=%s; verify effective config after olddefconfig' %
      ('y' if client else 'n', 'y' if server else 'n'))
