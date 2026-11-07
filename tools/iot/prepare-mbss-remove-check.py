#!/usr/bin/env python3
"""Extract staged MBSS remove into an injected host failure fixture."""
import argparse
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('driver', type=Path)
parser.add_argument('output', type=Path)
args = parser.parse_args()
if args.output.exists():
    raise SystemExit('New fixture output required')
source = (args.driver / 'ap/ap_mbss.c').read_text(encoding='utf-8')
signature = 'INT MBSS_Remove(RTMP_ADAPTER *pAd)'
if source.count(signature) != 1:
    raise SystemExit('Expected one checked MBSS removal')
start = source.index(signature)
function = source[start:source.index('\n}', start) + 2]
template = Path(__file__).with_name('mbss-remove-host-fixture.c.in').read_text(
    encoding='utf-8')
marker = '@@MBSS_REMOVE_FUNCTION@@'
if template.count(marker) != 1:
    raise SystemExit('Changed fixture marker')
args.output.write_text(template.replace(marker, function), encoding='utf-8')
print('Extracted MBSS removal refusal/retry fixture; not target proof')
