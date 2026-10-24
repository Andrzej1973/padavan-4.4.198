#!/usr/bin/env python3
"""Extract final assembled checked close into synthetic AP/PCI host fixture."""
import argparse
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('driver',type=Path);p.add_argument('output',type=Path)
a=p.parse_args()
if a.output.exists():raise SystemExit('New fixture output required')
s=(a.driver/'common/rtmp_init_inf.c').read_text(encoding='utf-8');sig='INT wr_iot_drv_close_checked('
if s.count(sig)!=1:raise SystemExit('Expected one final checked-close function')
start=s.index(sig);end=s.index('\n}',start)+2;f=s[start:end]
template=Path(__file__).with_name('checked-close-host-fixture.c.in').read_text(encoding='utf-8')
if template.count('@@CHECKED_CLOSE_FUNCTION@@')!=1:raise SystemExit('Changed fixture marker')
a.output.write_text(template.replace('@@CHECKED_CLOSE_FUNCTION@@',f),encoding='utf-8')
print('Extracted final checked close; AP/PCI primitives injected, not target proof')
