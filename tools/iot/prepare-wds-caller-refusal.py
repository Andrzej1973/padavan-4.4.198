#!/usr/bin/env python3
"""Stop WDS caller tails after insertion refusal; no returned-entry lifetime proof."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('source',type=Path);p.add_argument('output',type=Path)
a=p.parse_args();src=a.source.resolve(strict=True);out=a.output.resolve()
if out.exists() or src==out or src in out.parents or out in src.parents:p.error('new separate output required')
rel='ap/ap_wds.c';raw=(src/rel).read_bytes()
pin='b23842d8eda50289ed18aa017b26ae8eeb6b885be50cce7aa9016a0da00b697b'
if hashlib.sha256(raw).hexdigest()!=pin:p.error('unreviewed WDS source')
s=raw.decode()
rx='\t\t\tpEntry = MacTableInsertWDSEntry(pAd, pAddr, (UCHAR)WdsIdx);'
cfg='\t\tpEntry = MacTableInsertWDSEntry(pAd, wds_entry->PeerWdsAddr, index);'
assert s.count(rx)==s.count(cfg)==1
s=s.replace(rx,rx+'\n\t\t\tif (!pEntry) return NULL; /* No MCS update after refused insertion. */',1)
s=s.replace(cfg,cfg+'\n\t\tif (!pEntry) continue; /* Keep later configured links eligible. */',1)
shutil.copytree(src,out);(out/rel).write_text(s,encoding='utf-8',newline='\n')
out.with_name(out.name+'-caller-refusal.json').write_text(json.dumps({
 'input_sha256':pin,'output_sha256':hashlib.sha256((out/rel).read_bytes()).hexdigest(),
 'scope':'NULL insertion handling only; successful caller-tail lifetime still open',
 'target_compiled':False,'production_installed':False},indent=2)+'\n')
print('Staged RX return/configured-link continue after WDS insertion refusal')
