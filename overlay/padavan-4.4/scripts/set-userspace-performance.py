#!/usr/bin/env python3
"""Apply the requested size/performance policy to Padavan shared userspace flags."""
import argparse
from pathlib import Path
import re

parser = argparse.ArgumentParser()
parser.add_argument('trunk', type=Path)
parser.add_argument('config', type=Path)
args = parser.parse_args()
lines = args.config.read_text(encoding='utf-8').splitlines()
size = [line.strip() for line in lines if line.strip().startswith('CONFIG_CC_OPTIMIZE_FOR_SIZE=')]
if len(size) > 1:
    raise SystemExit('Duplicate size selector')
if size == ['CONFIG_CC_OPTIMIZE_FOR_SIZE=y']:
    print('Size optimization selected; shared userspace flags preserved')
    raise SystemExit(0)
if size and size != ['CONFIG_CC_OPTIMIZE_FOR_SIZE=n']:
    raise SystemExit('Unsupported size selector value')
if not size and '# CONFIG_CC_OPTIMIZE_FOR_SIZE is not set' not in lines:
    raise SystemExit('Explicit size/performance policy required')
path = args.trunk / 'config.arch'
source = path.read_text(encoding='utf-8')
for option in ['UOPT', 'LOPT']:
    pattern = r'^' + option + r'\s*=\s*-Os\s*$'
    if len(re.findall(pattern, source, re.M)) != 1:
        raise SystemExit('Inspect shared optimization assignment: ' + option)
    source = re.sub(pattern, option + ' = -O2', source, count=1, flags=re.M)
path.write_text(source, encoding='utf-8')
print('Shared userspace policy: UOPT=-O2 LOPT=-O2; package overrides require separate audit')

