#!/usr/bin/env python3
"""Inventory lexical peer-table mutation sites, not a complete C alias analysis."""
import argparse
import hashlib
import json
import re
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('candidate',type=Path);p.add_argument('output',type=Path)
a=p.parse_args();root=a.candidate.resolve(strict=True)
if a.output.exists():p.error('new output required')
def stripped(text):
 def blank(m):return ''.join('\n' if c=='\n' else ' ' for c in m.group())
 return re.sub(r'/\*.*?\*/|//[^\n]*|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'',blank,text,flags=re.S)
patterns={
 'entry_type_macro':r'\bSET_ENTRY_\w+\s*\(',
 'entry_type_assignment':r'\b\w+->EntryType\s*=(?!=)',
 'table_count_write':r'\bpAd->MacTab\.Size\s*(?:\+\+|--|=(?!=))',
 'table_clear':r'\bNdisZeroMemory\(\s*&pAd->MacTab(?:\.Size)?\s*,',
 'peer_reset_or_setup':r'\b(?:mac_entry_reset|tr_tb_reset_entry|tr_tb_set_entry)\s*\(',
}
rows=[];files={}
for file in sorted(root.rglob('*.c')):
 text=file.read_text(errors='replace');code=stripped(text)
 for kind,pattern in patterns.items():
  for m in re.finditer(pattern,code):
   rel=file.relative_to(root).as_posix()
   files[rel]=hashlib.sha256(file.read_bytes()).hexdigest()
   line_start=code.rfind('\n',0,m.start())+1
   declaration=bool(re.search(r'\b(?:VOID|BOOLEAN|INT)\s+$',code[line_start:m.start()]))
   rows.append({'file':rel,'line':code.count('\n',0,m.start())+1,
                'kind':kind,'declaration_not_call':declaration})
mgmt_source=(root/'mgmt/mgmt_entrytb.c').read_text()
mgmt=stripped(mgmt_source)
rept=stripped((root/'ap/ap_repeater.c').read_text())
def body(text,signature):
 start=text.index(signature);return text[start:text.index('\n}',start)+2]
def included_body(original,text,signature):
 if signature in text:return body(text,signature)
 for include in re.findall(r'#\s*include\s*"(wr-iot-[^"]+\.inc)"',original):
  path=root/'include'/include
  if not path.is_file():continue
  candidate=stripped(path.read_text())
  if signature not in candidate:continue
  rel=path.relative_to(root).as_posix()
  files[rel]=hashlib.sha256(path.read_bytes()).hexdigest()
  return body(candidate,signature)
 raise ValueError('function not found in source or included fragments: '+signature)
public_insert=included_body(mgmt_source,mgmt,'MAC_TABLE_ENTRY *MacTableInsertEntry(')
assert public_insert.index('wr_iot_peer_table_transaction_enter(')<public_insert.index('wr_iot_mac_insert_entry(')
assert public_insert.index('wr_iot_mac_insert_entry(')<public_insert.index('wr_iot_peer_table_transaction_leave(')
insert=body(mgmt,'MAC_TABLE_ENTRY *wr_iot_mac_insert_entry(')
rep_insert=body(rept,'MAC_TABLE_ENTRY *RTMPInsertRepeaterMacEntry(')
assert insert.index('NdisAcquireSpinLock(&pAd->MacTabLock);')<insert.index('mac_entry_reset(')
assert rep_insert.index('NdisAcquireSpinLock(&pAd->MacTabLock);')<rep_insert.index('NdisZeroMemory(pEntry, sizeof(MAC_TABLE_ENTRY));')
assert 'pAd->MacTab.Size ++;' in rep_insert and 'RTMP_STA_ENTRY_ADD(pAd, pEntry);' in rep_insert
easy=stripped((root/'easy_setup/mt7603_chip_ops.c').read_text())
easy_body=body(easy,'void ez_set_entry_apcli_mt7603(')
assert 'MacTableLookup(pAd, mac_addr)' in easy_body and 'SET_ENTRY_APCLI(pEntry)' in easy_body
assert easy_body.index('NdisAcquireSpinLock(&pAd->MacTabLock);')<easy_body.index('wr_iot_peer_table_allows(')
assert easy_body.index('wr_iot_peer_table_allows(')<easy_body.index('MacTableLookup(pAd, mac_addr)')
assert easy_body.index('MacTableLookup(pAd, mac_addr)')<easy_body.index('SET_ENTRY_APCLI(pEntry)')
assert easy_body.index('SET_ENTRY_APCLI(pEntry)')<easy_body.rindex('NdisReleaseSpinLock(&pAd->MacTabLock);')
inf=stripped((root/'common/rtmp_init_inf.c').read_text())
init=stripped((root/'common/rtmp_init.c').read_text())
clear_inf=len(re.findall(patterns['table_clear'],inf))
clear_init=len(re.findall(patterns['table_clear'],init))
assert clear_init>0
report={
 'scope':'lexical mutation seed inventory plus reviewed critical source assertions',
 'semantic_alias_analysis':False,'effective_feature_config_verified':False,
 'table_clear_sites':{'common/rtmp_init_inf.c':clear_inf,'common/rtmp_init.c':clear_init},
 'source_sha256':files,'sites':sorted(rows,key=lambda r:(r['file'],r['line'],r['kind'])),
 'critical_findings':[
  'main insertion holds MacTabLock while selecting/resetting/publishing peer; pre-lock size read is advisory',
  'RTMPInsertRepeaterMacEntry independently allocates same Content/TR slots and increments table size under MacTabLock',
  'repeater path cancels timers and clears entry memory before unchecked hardware entry add',
  'ez_set_entry_apcli_mt7603 admits under MacTabLock before mutating peer type; feature activation remains unverified',
  'fresh initialization and legacy/checked close clear whole MacTab; owner state must live outside that cleared memory',
  'reset preflight must reserve exclusive owner in same MacTabLock critical section; current observation is insufficient',
 ],
 'required_next_binding':[
  'adapter-owned fresh-only owner initialization outside MacTab',
  'main and repeater insertion plus easy-setup type mutation admission',
  'ordinary delete, WDS resume and explicit reset-owner deletion authorization',
  'reset reservation plus failed-setup preflight atomically under MacTabLock',
  'no timer/callback wait while MacTabLock/IRQ/transition locks held',
  'failed operation remains retained; no implicit clearing/reinitialization on retry',
  'full table clears and adapter release must obey owner lifetime',
 ],
 'production_installed':False,'target_compiled':False,'runtime_verified':False,
 'lifecycle_accepted':False,
}
a.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print('Inventoried '+str(len(rows))+' lexical sites in '+str(len(files))+' files; feature/alias/lifetime proof still open')
