#!/usr/bin/env python3
"""Extract the actual composed main ndo_open into a host failure-path fixture."""
import argparse
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('candidate', type=Path)
p.add_argument('output', type=Path)
a = p.parse_args()
source = (a.candidate / 'os/linux/rt_main_dev.c').read_text(encoding='utf-8')
signature = 'int MainVirtualIF_open(struct net_device *net_dev)'
if source.count(signature) != 1 or a.output.exists():
    p.error('main wrapper ambiguous or output already exists')
start = source.index(signature)
opening = source.index('{', start)
depth, end = 1, opening + 1
while depth:
    depth += (source[end] == '{') - (source[end] == '}')
    end += 1
actual = source[start:end]
if actual.count('VIRTUAL_IF_UP_CLAIM(pAd, net_dev, &ticket, generation)') != 1:
    p.error('composed main claim missing')
template = Path(__file__).with_name('composed-main-open-fixture.c.in').read_text(encoding='utf-8')
if template.count('/* ACTUAL_MAIN_OPEN */') != 1:
    p.error('fixture marker changed')
a.output.write_text(template.replace('/* ACTUAL_MAIN_OPEN */', actual), encoding='utf-8')
print('Extracted composed main open fixture:', a.output)
