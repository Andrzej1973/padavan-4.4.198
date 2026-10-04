#!/usr/bin/env python3
"""Acknowledge idempotent OFF on initialized candidate driver tables."""
import hashlib,sys
from pathlib import Path
root=Path(sys.argv[1])/'trunk/linux-4.4.x/drivers/net/wireless/mediatek'
items=[('mt76x2', 'BndStrg_Enable', '87f839ad153c333ac5df9cbb228bccfa3cf2b0261c0c37a5c4cf2bc7e69d96bb'), ('mt76x3', 'BndStrg_Tbl_Enable', 'ddf809d000e29771bad8e37ac50709aa5a74cf33138a9087ac27a0337a52e5d8')]
changes=[]
for chip,fn,expected in items:
 path=root/chip/'ap/ap_band_steering.c'
 text=path.read_text()
 start=text.index('INT '+fn+'(');end=text.index('\n}',start)+2
 original=text[start:end]
 if hashlib.sha256(original.encode()).hexdigest()!=expected:
  raise SystemExit('Pinned OFF function changed: '+chip+'; no files written')
 anchor='if (!(table->bEnabled ^ enable))'
 if original.count(anchor)!=1: raise SystemExit('OFF acknowledgement anchor changed')
 prepared=original.replace(anchor,anchor[:-1]+' && enable)')
 if chip=='mt76x2': prepared=prepared.replace('BNDSTRG_MSG msg;', 'BNDSTRG_MSG msg = { 0 };')
 changes.append((path,text[:start]+prepared+text[end:]))
for path,text in changes: path.write_text(text)
print('Both initialized drivers acknowledge repeated OFF; ownership/initialization guards preserved')
