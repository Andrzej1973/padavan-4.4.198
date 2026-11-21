#!/usr/bin/env python3
"""Bind reset ownership and peer mutator admission; full adapter clears unbound."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('source',type=Path);p.add_argument('output',type=Path)
a=p.parse_args();src=a.source.resolve(strict=True);out=a.output.resolve()
if out.exists() or src==out or src in out.parents or out in src.parents:p.error('new separate output required')
pins={
 'mgmt/mgmt_entrytb.c':'e6515864f6fc87950f269e1f79015bc67eda4a09f1b2dce2a51c7c5612e2617c',
 'include/rtmp.h':'27850a9cfd3f334a4f0c9b0b03958df0df400849ca7957df3995bdd9b01b4626',
 'common/rtmp_init.c':'9fc1d002acdc80e087c43686ed4088d18d1043d3b8cdef65d498f1c9a4ae0275',
 'ap/ap_repeater.c':'24e69448945f4967bff075097f42204fa0a67f29be49aaf0756a382dbdd1b2c9',
 'easy_setup/mt7603_chip_ops.c':'d8cfdc153de3044a1c50aa7e2997f943d62cfa195e3f40c672178041f0ba6bce',
}
for name,digest in pins.items():
 if hashlib.sha256((src/name).read_bytes()).hexdigest()!=digest:p.error('unreviewed predecessor: '+name)
texts={name:(src/name).read_text() for name in pins}
def one(s,old,new):
 if s.count(old)!=1:p.error('unreviewed anchor: '+old)
 return s.replace(old,new,1)
texts['include/rtmp.h']=one(texts['include/rtmp.h'],'#include "timer-task-owner.h"',
 '#include "timer-task-owner.h"\n#include "peer-table-owner.h"')
texts['include/rtmp.h']=one(texts['include/rtmp.h'],'\tUINT VirtualIfCnt;',
 '\tUINT VirtualIfCnt;\n struct wr_iot_peer_table_owner wr_iot_peer_table_owner;')
texts['common/rtmp_init.c']=one(texts['common/rtmp_init.c'],
 '\t\twr_iot_radio_transition_init(&pAd->wr_iot_transition);',
 '\t\twr_iot_peer_table_owner_init(&pAd->wr_iot_peer_table_owner);\n\t\twr_iot_radio_transition_init(&pAd->wr_iot_transition);')
for rel,sig in [('mgmt/mgmt_entrytb.c','MAC_TABLE_ENTRY *MacTableInsertEntry('),('ap/ap_repeater.c','MAC_TABLE_ENTRY *RTMPInsertRepeaterMacEntry(')]:
 s=texts[rel];start=s.index(sig);end=s.index('\n}',start)+2;body=s[start:end]
 lock='NdisAcquireSpinLock(&pAd->MacTabLock);'
 body=one(body,lock,lock+'\n#include "wr-iot-peer-table-insertion-gate.inc"')
 texts[rel]=s[:start]+body+s[end:]
s=texts['mgmt/mgmt_entrytb.c']
s=one(s,'unsigned long wr_resume_serial)\n{','unsigned long wr_resume_serial, unsigned long wr_table_serial)\n{')
start=s.index('static BOOLEAN wr_iot_mac_delete_entry(');end=s.index('\n}',start)+2;body=s[start:end]
body=one(body,'NdisAcquireSpinLock(&pAd->MacTabLock);',
 'NdisAcquireSpinLock(&pAd->MacTabLock);\n#include "wr-iot-peer-table-delete-gate.inc"')
s=s[:start]+body+s[end:]
s=one(s,'return wr_iot_mac_delete_entry(pAd, wcid, pAddr, NULL, 0, 0);',
 'return wr_iot_mac_delete_entry(pAd, wcid, pAddr, NULL, 0, 0, 0);')
s=one(s,'return wr_iot_mac_delete_entry(pAd, wcid, pAddr, device, generation, serial);',
 'return wr_iot_mac_delete_entry(pAd, wcid, pAddr, device, generation, serial, 0);')
s=one(s,'#include "wr-iot-peer-failed-reset-preflight.inc"','#include "wr-iot-peer-table-reset-owner.inc"')
for sig,scope in [('BOOLEAN MacTableReset(', 'NULL'),('BOOLEAN MacTableResetWdev(', 'wdev')]:
 start=s.index(sig);end=s.index('\n}',start)+2;body=s[start:end]
 body=one(body,'\tMAC_TABLE_ENTRY *pMacEntry;', '\tMAC_TABLE_ENTRY *pMacEntry;\n unsigned long wr_table_serial;')
 body=one(body,'if (wr_iot_reset_has_failed_setup(pAd,'+scope+')) return FALSE;',
 'wr_table_serial=wr_iot_peer_reset_begin(pAd,'+scope+');\n if (!wr_table_serial) return FALSE;')
 # All post-reservation failures retain ownership; only no-reservation returns directly.
 body=body.replace('return FALSE;','return wr_iot_peer_reset_finish(pAd,wr_table_serial,FALSE);')
 body=one(body,'if (!wr_table_serial) return wr_iot_peer_reset_finish(pAd,wr_table_serial,FALSE);',
 'if (!wr_table_serial) return FALSE;')
 body=one(body,'MacTableDeleteEntry(pAd, i, pMacEntry->Addr)',
 'wr_iot_mac_delete_entry(pAd, i, pMacEntry->Addr, NULL, 0, 0, wr_table_serial)')
 body=one(body,'return TRUE;', 'return wr_iot_peer_reset_finish(pAd,wr_table_serial,TRUE);')
 s=s[:start]+body+s[end:]
texts['mgmt/mgmt_entrytb.c']=s
s=texts['easy_setup/mt7603_chip_ops.c'];start=s.index('void ez_set_entry_apcli_mt7603(');end=s.index('\n}',start)+2;body=s[start:end]
body=one(body,'pEntry = MacTableLookup(pAd, mac_addr);',
 '''NdisAcquireSpinLock(&pAd->MacTabLock);
 if (!wr_iot_peer_table_allows(&pAd->wr_iot_peer_table_owner,0)) {
  NdisReleaseSpinLock(&pAd->MacTabLock);return;
 }
 pEntry = MacTableLookup(pAd, mac_addr);''')
# Release before the original terminal return, not after it.
body=one(body,'\treturn;\t', '\tNdisReleaseSpinLock(&pAd->MacTabLock);\n\treturn;\t')
texts['easy_setup/mt7603_chip_ops.c']=s[:start]+body+s[end:]
shutil.copytree(src,out)
for name,text in texts.items():(out/name).write_text(text,encoding='utf-8',newline='\n')
for local,target in [('peer-table-owner.h','peer-table-owner.h'),('peer-table-insertion-gate.inc','wr-iot-peer-table-insertion-gate.inc'),('peer-table-delete-gate.inc','wr-iot-peer-table-delete-gate.inc'),('peer-table-reset-owner.inc','wr-iot-peer-table-reset-owner.inc')]:
 shutil.copyfile(Path(__file__).with_name(local),out/'include'/target)
out.with_name(out.name+'-peer-table-owner.json').write_text(json.dumps({
 'input_sha256':pins,'output_sha256':{name:hashlib.sha256((out/name).read_bytes()).hexdigest() for name in pins},
 'scope':'reset reservation and peer mutation admission; full table clear/release bypasses remain',
 'target_compiled':False,'runtime_verified':False,'lifecycle_accepted':False,'full_table_clear_owner_bound':False,
},indent=2)+'\n',encoding='utf-8')
print('Staged reset/table mutation owner; full clears and lifetime still unbound')
