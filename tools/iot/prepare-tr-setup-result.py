#!/usr/bin/env python3
"""Propagate pre-queue WTBL setup failure in isolated candidate."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('source', type=Path)
p.add_argument('output', type=Path)
a = p.parse_args()
src = a.source.resolve(strict=True); out = a.output.resolve()
if out.exists() or src == out or src in out.parents or out in src.parents:
    p.error('new separate output required')
pins = {'mgmt/mgmt_entrytb.c':'2c9c9c36068a9b96713af95f67947f1e1c9845e6664d68ca44c67cfe7432f334',
        'include/rtmp.h':'8b7d18842ffd0cae866b3cfc7e28a6e38691577641c8e4da11712d6cc065b829'}
for name, sha in pins.items():
    if hashlib.sha256((src/name).read_bytes()).hexdigest()!=sha:
        p.error('unreviewed input: '+name)
s=(src/'mgmt/mgmt_entrytb.c').read_text()
start=s.index('VOID tr_tb_set_entry('); end=s.index('VOID tr_tb_set_mcast_entry(',start)
body=s[start:end].replace('VOID tr_tb_set_entry(', 'BOOLEAN tr_tb_set_entry(',1)
assert body.count('return;')==1
body=body.replace('return;', 'return FALSE;',1)
# Both successful initialization and out-of-range refusal return explicitly.
anchor='\n\t}\n\n}\n'
assert body.count(anchor)==1
body=body.replace(anchor,'\n\t\treturn TRUE;\n\t}\n\treturn FALSE;\n}\n',1)
s=s[:start]+body+s[end:]
anchor='\tSTA_TR_ENTRY *tr_entry = NULL;'
insert=s.index('MAC_TABLE_ENTRY *MacTableInsertEntry(')
before=s[:insert]; tail=s[insert:]
assert tail.count(anchor)==1
tail=tail.replace(anchor,anchor+'\n#ifdef CONFIG_AP_SUPPORT\n\tBOOLEAN wr_iot_client_counted = FALSE;\n#endif',1)
anchor='\t\t\t\t\tpAd->ApCfg.EntryClientCount++;'
assert tail.count(anchor)==1
tail=tail.replace(anchor,anchor+'\n\t\t\t\t\twr_iot_client_counted = TRUE;',1)
old='\t\t\ttr_tb_set_entry(pAd, i, pEntry);'
new='''\t\t\tif (!tr_tb_set_entry(pAd, i, pEntry)) {
\t\t\t\t/* Failure precedes queue-lock/timer allocation and hash publication. */
#ifdef CONFIG_AP_SUPPORT
\t\t\t\tif (wr_iot_client_counted) {
\t\t\t\t\tpAd->ApCfg.MBSSID[pEntry->func_tb_idx].StaCount--;
\t\t\t\t\tpAd->ApCfg.EntryClientCount--;
\t\t\t\t}
#endif
\t\t\t\t{
\t\t\t\t\tULONG wr_iot_flags;
\t\t\t\t\tRTMP_IRQ_LOCK(&pAd->irq_lock, wr_iot_flags);
\t\t\t\t\tWRITE_ONCE(tr_entry->enq_cap, FALSE);
\t\t\t\t\tWRITE_ONCE(tr_entry->deq_cap, FALSE);
\t\t\t\t\tRTMP_IRQ_UNLOCK(&pAd->irq_lock, wr_iot_flags);
\t\t\t\t}
\t\t\t\tSET_ENTRY_NONE(tr_entry);
\t\t\t\tSET_ENTRY_NONE(pEntry);
\t\t\t\tNdisReleaseSpinLock(&pAd->MacTabLock);
\t\t\t\treturn NULL;
\t\t\t}'''
assert tail.count(old)==1
s=before+tail.replace(old,new,1)
h=(src/'include/rtmp.h').read_text()
assert h.count('VOID tr_tb_set_entry(')==1
h=h.replace('VOID tr_tb_set_entry(','BOOLEAN tr_tb_set_entry(',1)
shutil.copytree(src,out)
for name,text in [('mgmt/mgmt_entrytb.c',s),('include/rtmp.h',h)]:
    (out/name).write_text(text,encoding='utf-8',newline='\n')
out.with_name(out.name+'-setup-result.json').write_text(json.dumps({
    'input_sha256':pins,'output_sha256':{n:hashlib.sha256((out/n).read_bytes()).hexdigest() for n in pins},
    'scope':'pre-queue failure status and counted-client rollback only',
    'borrowed_apcli_resources_freed':False,'target_compiled':False,
    'production_installed':False,'full_peer_lifetime_proved':False},indent=2)+'\n')
print('Staged WTBL failure propagation; target and lifetime acceptance open')
