#!/usr/bin/env python3
"""Preserve lazy WDS table on MAC deletion refusal; not an atomic age-out protocol."""
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
pin='cbc6fcc68157616e595c9afff533d34e9495755f2dcdba7c23228df4b3507d5e'
if hashlib.sha256(raw).hexdigest()!=pin:p.error('unreviewed maintenance input')
s=raw.decode()
old='\t\t\t\tWdsEntryDel(pAd, pEntry->Addr);\n\t\t\t\tMacTableDeleteWDSEntry(pAd, pEntry->wcid, pEntry->Addr);'
new='''\t\t\t\tUCHAR wr_addr[MAC_ADDR_LEN];
\t\t\t\tUSHORT wr_wcid = pEntry->wcid;
\t\t\t\tCOPY_MAC_ADDR(wr_addr, pEntry->Addr);
\t\t\t\tif (MacTableDeleteWDSEntry(pAd, wr_wcid, wr_addr))
\t\t\t\t\tWdsEntryDel(pAd, wr_addr);'''
assert s.count(old)==1
s=s.replace(old,new,1)
shutil.copytree(src,out);(out/rel).write_text(s,encoding='utf-8',newline='\n')
out.with_name(out.name+'-maintenance-refusal.json').write_text(json.dumps({
 'input_sha256':pin,'output_sha256':hashlib.sha256((out/rel).read_bytes()).hexdigest(),
 'scope':'lazy age-out refusal ordering; snapshot/reuse atomicity not proved',
 'target_compiled':False,'production_installed':False},indent=2)+'\n')
print('Staged lazy WDS table cleanup only after accepted peer deletion')
