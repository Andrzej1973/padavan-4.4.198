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
# Apply the central selector to the board kernel config before firmware build.
kernel = args.trunk / 'configs/boards/WR1200JS/kernel-4.4.x.config'
kernel_source = kernel.read_text(encoding='utf-8')
kernel_pattern = r'^(?:CONFIG_CC_OPTIMIZE_FOR_SIZE=.*|# CONFIG_CC_OPTIMIZE_FOR_SIZE is not set)$'
kernel_value = ('CONFIG_CC_OPTIMIZE_FOR_SIZE=y' if size == ['CONFIG_CC_OPTIMIZE_FOR_SIZE=y']
                else '# CONFIG_CC_OPTIMIZE_FOR_SIZE is not set')
if size and size not in (['CONFIG_CC_OPTIMIZE_FOR_SIZE=y'], ['CONFIG_CC_OPTIMIZE_FOR_SIZE=n']):
    raise SystemExit('Unsupported size selector value')
if len(re.findall(kernel_pattern, kernel_source, re.M)) != 1:
    raise SystemExit('Inspect kernel optimization selector')
kernel.write_text(re.sub(kernel_pattern, kernel_value, kernel_source,
                         count=1, flags=re.M), encoding='utf-8')
if size == ['CONFIG_CC_OPTIMIZE_FOR_SIZE=y']:
    print('Size optimization selected; shared userspace flags preserved')
    raise SystemExit(0)
if size and size != ['CONFIG_CC_OPTIMIZE_FOR_SIZE=n']:
    raise SystemExit('Unsupported size selector value')
if not size and not any(line.strip() in ('# CONFIG_CC_OPTIMIZE_FOR_SIZE is not set', '# CONFIG_CC_OPTIMIZE_FOR_SIZE=y') for line in lines):
    raise SystemExit('Explicit size/performance policy required')
path = args.trunk / 'config.arch'
source = path.read_text(encoding='utf-8')
for option in ['UOPT', 'LOPT']:
    pattern = r'^' + option + r'\s*=\s*-Os\s*$'
    if len(re.findall(pattern, source, re.M)) != 1:
        raise SystemExit('Inspect shared optimization assignment: ' + option)
    source = re.sub(pattern, option + ' = -O2', source, count=1, flags=re.M)
busybox = args.trunk / 'user/busybox/busybox-1.24.x/Makefile.flags'
busy_source = busybox.read_text(encoding='utf-8')
busy_anchor = 'CFLAGS += $(call cc-option,-Os,$(call cc-option,-O2,))'
if busy_source.count(busy_anchor) != 2:
    raise SystemExit('Inspect BusyBox target optimization anchors')
busy_source = busy_source.replace(busy_anchor, 'CFLAGS += $(call cc-option,-O2,)')
# Check both source contracts before changing either file.
path.write_text(source, encoding='utf-8')
busybox.write_text(busy_source, encoding='utf-8')
print('Performance policy: UOPT=-O2 LOPT=-O2 BusyBox target=-O2; other package overrides require separate audit')

