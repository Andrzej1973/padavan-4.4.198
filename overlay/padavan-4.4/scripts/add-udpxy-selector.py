#!/usr/bin/env python3
"""Allow excluding UDPXY instead of silently falling back from msd_lite."""
import sys
from pathlib import Path

root = Path(sys.argv[1]) / 'trunk'
make = root / 'user/Makefile'
net = root / 'user/rc/net.c'
text = make.read_text()
code = net.read_text()
old = 'ifneq ($(CONFIG_FIRMWARE_INCLUDE_MSD_LITE),y)\ndir_y\t\t\t\t\t\t+= udpxy\nendif'
new = 'ifeq ($(CONFIG_FIRMWARE_INCLUDE_UDPXY),y)\n' + old + '\nendif'
anchor = 'start_udpxy(char *wan_ifname)\n{\n'
if text.count(old) != 1 or code.count(anchor) != 1:
    raise SystemExit('UDPXY build/lifecycle anchors changed; no files written')
templates = sorted((root / 'configs/templates').glob('*.config'))
if not templates or any('CONFIG_FIRMWARE_INCLUDE_UDPXY=' in p.read_text() for p in templates):
    raise SystemExit('UDPXY template state changed; no files written')
make.write_text(text.replace(old, new))
net.write_text(code.replace(anchor, anchor +
    '\tif (!check_if_file_exist("/usr/sbin/udpxy") &&\n'
    '\t    !check_if_file_exist("/usr/bin/msd_lite"))\n\t\treturn;\n'))
for path in templates:
    with path.open('a') as output:
        output.write('\n### Include UDPXY when msd_lite is not selected.\nCONFIG_FIRMWARE_INCLUDE_UDPXY=y\n')
print('Registered UDPXY selector; existing other-board defaults preserved')
