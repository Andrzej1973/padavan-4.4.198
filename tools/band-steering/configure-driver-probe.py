#!/usr/bin/env python3
"""Enable actual Padavan wrapper symbols only in an isolated kernel copy."""
import argparse
import hashlib
import json
from pathlib import Path
import re

parser = argparse.ArgumentParser()
parser.add_argument('kernel', type=Path)
args = parser.parse_args()
kernel = args.kernel
checks = [('mt76x3_ap', 'MT7603E_BAND_STEERING_7603'),
          ('mt76x2_ap', 'RT_BAND_STEERING')]
cfg = kernel / '.config'
before = cfg.read_bytes()
text = before.decode('utf-8')
for driver, symbol in checks:
    folder = kernel / 'drivers/net/wireless/mediatek' / driver
    kconfig = (folder / 'Kconfig').read_text()
    makefile = (folder / 'Makefile').read_text()
    if not re.search(r'^config ' + symbol + r'$', kconfig, re.M):
        raise ValueError('Missing active wrapper Kconfig: ' + symbol)
    if 'ifeq ($(CONFIG_' + symbol + '),y)' not in makefile or '-DBAND_STEERING' not in makefile:
        raise ValueError('Missing wrapper compile hook: ' + symbol)
    old = '# CONFIG_' + symbol + ' is not set'
    if text.splitlines().count(old) != 1:
        raise ValueError('Expected disabled baseline selector: ' + symbol)
    text = text.replace(old, 'CONFIG_' + symbol + '=y')
for symbol in ('CONFIG_MT76X3_AP=m', 'CONFIG_MT76X2_AP=m'):
    if text.splitlines().count(symbol) != 1:
        raise ValueError('WR1200JS module configuration changed: ' + symbol)
with cfg.open('w', encoding='utf-8', newline='\n') as out:
    out.write(text)
report = {'runtime_verified': False,
          'symbols': ['CONFIG_' + symbol for _, symbol in checks],
          'before_sha256': hashlib.sha256(before).hexdigest(),
          'after_sha256': hashlib.sha256(cfg.read_bytes()).hexdigest()}
(kernel / 'band-steering-driver-config.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
