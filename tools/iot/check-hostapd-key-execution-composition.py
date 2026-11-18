#!/usr/bin/env python3
"""Check reversible native key factoring and the single trusted-copy boundary."""
import argparse,runpy
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);a=p.parse_args()
here=Path(__file__).resolve().parent
native=(a.source/'ap/ap_cfg.c').read_text()
base=runpy.run_path(str(here/'hostapd-key-copy-composition.py'))['compose'](native)
compose=runpy.run_path(str(here/'hostapd-key-execution-composition.py'))['compose']
result,helpers,receipts=compose(base)
restored=result.replace(helpers+'\n','',1)
for old,new in receipts:
 assert restored.count(new)==1;restored=restored.replace(new,old,1)
assert restored==base
assert result.count('copy_from_user(&Key,')==1
assert result.count('copy_from_user(&delkey,')==1
assert 'copy_from_user' not in helpers and 'MacTableLookup' not in helpers
for bad in (result,base.replace('if (Status) { Status = -EFAULT; break; }','',1)):
 try:compose(bad)
 except ValueError:pass
 else:raise AssertionError('duplicate or unsafe-copy input accepted')
print('Native key factoring: byte restoration, single copy, no helper relookup and malformed/duplicate refusal PASS; target/native execution not checked')
