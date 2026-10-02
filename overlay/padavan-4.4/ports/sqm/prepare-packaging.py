#!/usr/bin/env python3
import argparse
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('target', type=Path)
a = p.parse_args()
configure = a.target / 'trunk/configure'
text = configure.read_text(encoding='utf-8')
begin = text.index('# SQM QOS')
end = text.index('\nfi', begin)
section = text[begin:end]
anchor = 'func_enable_kernel_param "CONFIG_IFB"'
if section.count(anchor) != 1 or anchor + ' "m"' in section:
    raise SystemExit('Unexpected SQM kernel configuration rules')
section = section.replace(anchor, anchor + ' "m"')
configure.write_text(text[:begin] + section + text[end:], encoding='utf-8')
template = a.target / 'trunk/configs/templates/WR1200JS.config'
text = template.read_text(encoding='utf-8')
if 'CONFIG_FIRMWARE_INCLUDE_SQM=' not in text:
    template.write_text(text.rstrip() + '\nCONFIG_FIRMWARE_INCLUDE_SQM=n\n', encoding='utf-8')
print('SQM packaging prepared; IFB remains a module')
