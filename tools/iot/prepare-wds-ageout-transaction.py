#!/usr/bin/env python3
"""Bind lazy WDS age-out reservation through exact-slot cleanup in a candidate."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('source',type=Path);p.add_argument('output',type=Path)
a=p.parse_args();src=a.source.resolve(strict=True);out=a.output.resolve()
if out.exists() or src==out or src in out.parents or out in src.parents:
    p.error('new separate output required')
receipt=json.loads(src.with_name(src.name+'-delete-identity.json').read_text())
if hashlib.sha256((src/'include/wr-iot-wds-peer-delete-gate.inc').read_bytes()).hexdigest()!=receipt['helper_sha256']:
    p.error('delete-identity predecessor mismatch')
raw=(src/'ap/ap_wds.c').read_bytes();s=raw.decode()
old='''\t\t\t\tUCHAR wr_addr[MAC_ADDR_LEN];
\t\t\t\tUSHORT wr_wcid = pEntry->wcid;
\t\t\t\tCOPY_MAC_ADDR(wr_addr, pEntry->Addr);
\t\t\t\tif (MacTableDeleteWDSEntry(pAd, wr_wcid, wr_addr))
\t\t\t\t\tWdsEntryDel(pAd, wr_addr);'''
if s.count(old)!=1:p.error('unreviewed lazy age-out layout')
s=s.replace(old,'\t\t\t\t(void)wr_iot_wds_ageout(pAd, idx);',1)
anchor='VOID WdsTableMaintenance(RTMP_ADAPTER *pAd)'
if s.count(anchor)!=1:p.error('unreviewed maintenance entry')
s=s.replace(anchor,'#include "wr-iot-wds-ageout-transaction.inc"\n\n'+anchor,1)
start=s.index(anchor);end=s.index('\nVOID RT28xx_WDS_Close',start)
maintenance=s[start:end]
entry='\tUCHAR idx;'
if maintenance.count(entry)!=1:p.error('unreviewed maintenance declarations')
maintenance=maintenance.replace(entry,entry+'''

\tif (pAd->WdsTab.Mode == WDS_LAZY_MODE) {
\t\twr_iot_wds_lazy_maintenance(pAd);
\t\treturn;
\t}''',1)
old_loop='for (idx = 0; idx < pAd->WdsTab.Size; idx++)'
if maintenance.count(old_loop)!=1:p.error('unreviewed maintenance loop')
maintenance=maintenance.replace(old_loop,'for (idx = 0; idx < MAX_WDS_ENTRY; idx++)',1)
old_access='\t\tPMAC_TABLE_ENTRY pEntry = &pAd->MacTab.Content[wcid];'
new_access='''\t\tPMAC_TABLE_ENTRY pEntry;
\t\tif (!pAd->WdsTab.WdsEntry[idx].Valid || !wcid || wcid >= MAX_LEN_OF_MAC_TABLE)
\t\t\tcontinue;
\t\tpEntry = &pAd->MacTab.Content[wcid];'''
if maintenance.count(old_access)!=1:p.error('unreviewed WCID lookup')
maintenance=maintenance.replace(old_access,new_access,1)
s=s[:start]+maintenance+s[end:]
shutil.copytree(src,out)
(out/'ap/ap_wds.c').write_text(s,encoding='utf-8',newline='\n')
helper=Path(__file__).with_name('wds-ageout-transaction.inc')
shutil.copyfile(helper,out/'include/wr-iot-wds-ageout-transaction.inc')
out.with_name(out.name+'-ageout-transaction.json').write_text(json.dumps({
 'input_sha256':hashlib.sha256(raw).hexdigest(),
 'output_sha256':hashlib.sha256((out/'ap/ap_wds.c').read_bytes()).hexdigest(),
 'helper_sha256':hashlib.sha256(helper.read_bytes()).hexdigest(),
 'scope':'lazy age-out reservation and terminal-state check; recovery/DMA/TxS still open',
 'target_compiled':False,'production_installed':False,
},indent=2)+'\n')
print('Staged exact-slot WDS lazy age-out transaction')
