#!/usr/bin/env python3
"""Apply the selected Privoxy port in a deterministic prepared-source order."""
import argparse
from pathlib import Path
import subprocess
import sys

parser = argparse.ArgumentParser()
parser.add_argument('tree', type=Path)
parser.add_argument('--config', required=True, type=Path)
args = parser.parse_args()
selected = [line.strip() for line in args.config.read_text(encoding='utf-8').splitlines()
            if line.strip().startswith('CONFIG_FIRMWARE_INCLUDE_PRIVOXY=')]
if selected != ['CONFIG_FIRMWARE_INCLUDE_PRIVOXY=y']:
    raise SystemExit('One explicit Privoxy=y selection required')
trunk = args.tree.resolve() / 'trunk'
busybox = (trunk / 'configs/boards/busybox.config').read_text(encoding='utf-8').splitlines()
for key in ['FLOCK', 'PIDOF', 'AWK', 'ASH']:
    if 'CONFIG_' + key + '=y' not in busybox:
        raise SystemExit('Privoxy lifecycle prerequisite missing: ' + key)
assets = Path(__file__).resolve().parent
httpd = trunk / 'user/httpd'
for script, target in [('integrate-build.py', args.tree.resolve()),
                       ('extend-event-bank.py', httpd),
                       ('register-http-fields.py', httpd),
                       ('register-file-routing.py', httpd / 'web_ex.c'),
                       ('reject-incomplete-apply.py', httpd / 'web_ex.c'),
                       ('register-ui.py', trunk)]:
    subprocess.run([sys.executable, str(assets / script), str(target)], check=True)
print('Privoxy full source port applied; image and runtime checks remain required')
