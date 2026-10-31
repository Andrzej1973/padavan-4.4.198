#!/usr/bin/env python3
"""Extract the staged PCI suspend pre-mutation fence into a host fixture."""
import argparse
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('driver', type=Path)
p.add_argument('output', type=Path)
a = p.parse_args()
if a.output.exists():
    raise SystemExit('Fixture output must be new')
source = (a.driver / 'os/linux/pci_main_dev.c').read_text(encoding='utf-8')
signature = 'static int rt_pci_suspend(struct pci_dev *pci_dev, pm_message_t state)'
if source.count(signature) != 1:
    raise SystemExit('Expected one PCI suspend function')
function = source[source.index(signature):]
function = function[:function.index('\n}') + 2]
first = '\t\t\tULONG wr_iot_flags;'
last = '\t\t\t/* avoid users do suspend after interface is down */'
if function.count(first) != 1 or function.count(last) != 1:
    raise SystemExit('Changed PM fence extraction boundary')
fragment = function[function.index(first):function.index(last)]
template = Path(__file__).with_name('pci-pm-fence-host-fixture.c.in').read_text(encoding='utf-8')
marker = '@@PCI_PM_FENCE@@'
if template.count(marker) != 1:
    raise SystemExit('Changed fixture marker')
a.output.write_text(template.replace(marker, fragment), encoding='utf-8')
print('Extracted PCI pre-mutation PM fence; not target proof')
