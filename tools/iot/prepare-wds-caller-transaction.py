#!/usr/bin/env python3
"""Move WDS caller MCS/rate tails inside the existing counted transaction."""
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
s=raw.decode()
# The input receipt and preparer's exact predecessor pin authenticate source.
receipt=json.loads(src.with_name(src.name+'-caller-refusal.json').read_text())
if hashlib.sha256(raw).hexdigest()!=receipt['output_sha256']:p.error('predecessor receipt mismatch')
rxstart=s.index('MAC_TABLE_ENTRY *FindWdsEntry(');rxend=s.index('VOID WdsTableMaintenance(',rxstart)
cfgstart=s.index('VOID AsicUpdateWdsRxWCIDTable(');cfgend=s.index('VOID AsicUpdateWdsEncryption(',cfgstart)
rx=s[rxstart:rxend];cfg=s[cfgstart:cfgend]
mcsstart=cfg.index('\t\tRTMPSetSupportMCS(')
mcsend=cfg.index('sizeof(pAd->CommonCfg.HtCapability));',mcsstart)+len('sizeof(pAd->CommonCfg.HtCapability));')
switchstart=cfg.index('\t\tswitch (wds_entry->wdev.PhyMode)',mcsend)
switchend=cfg.rfind('\n\t}\n\n\treturn;')
assert switchend>switchstart
mcs=cfg[mcsstart:mcsend];rate=cfg[switchstart:switchend]
helper='''static VOID wr_iot_wds_finish_peer(RTMP_ADAPTER *pAd, MAC_TABLE_ENTRY *pEntry, UINT index, UINT mode)
{
 RT_802_11_WDS_ENTRY *wds_entry = &pAd->WdsTab.WdsEntry[index];
 if (!pEntry || !mode) return;
'''+mcs+'\n if (mode == 2) {\n'+rate+'\n }\n}\n\n'
rxmcs=rx.index('\t\t\tRTMPSetSupportMCS(')
rxmcse=rx.index('sizeof(pAd->CommonCfg.HtCapability));',rxmcs)+len('sizeof(pAd->CommonCfg.HtCapability));')
rx=rx[:rxmcs]+rx[rxmcse:]
rx=rx.replace('MacTableInsertWDSEntry(pAd, pAddr, (UCHAR)WdsIdx)',
              'wr_iot_wds_insert_transaction(pAd, pAddr, (UCHAR)WdsIdx, 1)',1)
cfg=cfg[:mcsstart]+cfg[mcsend:switchstart]+cfg[switchend:]
cfg=cfg.replace('MacTableInsertWDSEntry(pAd, wds_entry->PeerWdsAddr, index)',
                'wr_iot_wds_insert_transaction(pAd, wds_entry->PeerWdsAddr, index, 2)',1)
s=s[:cfgstart]+cfg+s[cfgend:]
s=s[:rxstart]+rx+s[rxend:]
signature='MAC_TABLE_ENTRY *MacTableInsertWDSEntry(RTMP_ADAPTER *pAd, UCHAR *pAddr, UINT WdsTabIdx)'
assert s.count(signature)==1
start=s.index(signature);end=s.index('\n}',start)+2
wrapper=s[start:end].replace(signature,
 'static MAC_TABLE_ENTRY *wr_iot_wds_insert_transaction(RTMP_ADAPTER *pAd, UCHAR *pAddr, UINT WdsTabIdx, UINT finish_mode)',1)
anchor=' result = wr_iot_wds_insert_body(pAd, pAddr, WdsTabIdx);'
assert wrapper.count(anchor)==1
wrapper=wrapper.replace(anchor,anchor+'\n if (result) wr_iot_wds_finish_peer(pAd, result, WdsTabIdx, finish_mode);',1)
compat='\n\n'+signature+'\n{\n return wr_iot_wds_insert_transaction(pAd, pAddr, WdsTabIdx, 0);\n}\n'
s=s[:start]+helper+wrapper+compat+s[end:]
shutil.copytree(src,out);(out/rel).write_text(s,encoding='utf-8',newline='\n')
out.with_name(out.name+'-caller-transaction.json').write_text(json.dumps({
 'input_sha256':hashlib.sha256(raw).hexdigest(),'output_sha256':hashlib.sha256((out/rel).read_bytes()).hexdigest(),
 'scope':'MCS/rate caller tails within counted insertion; returned pointer/adapter lifetime still open',
 'target_compiled':False,'production_installed':False},indent=2)+'\n')
print('Staged RX/configured peer finishing inside counted WDS transaction')
