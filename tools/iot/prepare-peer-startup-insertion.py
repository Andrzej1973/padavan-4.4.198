#!/usr/bin/env python3
"""Add explicit WDS startup insertion entry; caller lease/WDS chain unbound."""
import argparse,hashlib,json,shutil
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('source',type=Path);p.add_argument('output',type=Path)
a=p.parse_args();src=a.source.resolve(strict=True);out=a.output.resolve()
if out.exists() or src==out or src in out.parents or out in src.parents:p.error('new separate output required')
pins={'mgmt/mgmt_entrytb.c':'ddb7a7b574feb06a652ff5ad19675aa8c23301f1e22b0895c0bc6e5a2c668ab1',
 'include/rtmp.h':'42ebf6a4245ce395eb5ad4b14d8976f80c19ed8a24e47fddec906db77180023c'}
texts={}
for n,h in pins.items():
 if hashlib.sha256((src/n).read_bytes()).hexdigest()!=h:p.error('unreviewed predecessor: '+n)
 texts[n]=(src/n).read_text()
def one(s,old,new):
 if s.count(old)!=1:p.error('unreviewed anchor: '+old)
 return s.replace(old,new,1)
s=texts['mgmt/mgmt_entrytb.c'];start=s.index('MAC_TABLE_ENTRY *MacTableInsertEntry(')
end=s.index('\n}',start)+2;body=s[start:end]
body=one(body,'MAC_TABLE_ENTRY *MacTableInsertEntry(', 'static MAC_TABLE_ENTRY *wr_iot_mac_insert_entry(')
body=one(body,'IN BOOLEAN CleanAll)', 'IN BOOLEAN CleanAll,\n const struct wr_iot_peer_open_ticket *wr_open_ticket,unsigned long wr_open_lease)')
body=one(body,'#include "wr-iot-peer-table-insertion-gate.inc"', '#include "wr-iot-peer-startup-insertion-gate.inc"')
wrapper='''
MAC_TABLE_ENTRY *MacTableInsertEntry(RTMP_ADAPTER *pAd,UCHAR *pAddr,
 struct wifi_dev *wdev,UINT32 ent_type,UCHAR OpMode,BOOLEAN CleanAll)
{
 return wr_iot_mac_insert_entry(pAd,pAddr,wdev,ent_type,OpMode,CleanAll,NULL,0);
}
MAC_TABLE_ENTRY *wr_iot_mac_insert_startup_wds(RTMP_ADAPTER *pAd,UCHAR *pAddr,
 struct wifi_dev *wdev,const struct wr_iot_peer_open_ticket *ticket,unsigned long lease)
{
 if(!pAd||!pAddr||!wdev||!ticket||!lease)return NULL;
 return wr_iot_mac_insert_entry(pAd,pAddr,wdev,ENTRY_WDS,OPMODE_AP,TRUE,ticket,lease);
}
'''
texts['mgmt/mgmt_entrytb.c']=s[:start]+body+wrapper+s[end:]
prototype='''MAC_TABLE_ENTRY *wr_iot_mac_insert_startup_wds(RTMP_ADAPTER *pAd,UCHAR *pAddr,
 struct wifi_dev *wdev,const struct wr_iot_peer_open_ticket *ticket,unsigned long lease);
'''
texts['include/rtmp.h']=one(texts['include/rtmp.h'],'MAC_TABLE_ENTRY *MacTableInsertEntry(',prototype+'\nMAC_TABLE_ENTRY *MacTableInsertEntry(')
shutil.copytree(src,out)
for n,s in texts.items():(out/n).write_text(s,encoding='utf-8',newline='\n')
shutil.copyfile(Path(__file__).with_name('peer-startup-insertion-gate.inc'),out/'include/wr-iot-peer-startup-insertion-gate.inc')
shutil.copyfile(Path(__file__).with_name('peer-open-owner.h'),out/'include/peer-open-owner.h')
out.with_name(out.name+'-startup-insertion.json').write_text(json.dumps({
 'input_sha256':pins,'output_sha256':{n:hashlib.sha256((out/n).read_bytes()).hexdigest() for n in pins},
 'scope':'private insertion authorization and public wrappers; lease claim caller/WDS chain absent',
 'wds_caller_bound':False,'target_compiled':False,'runtime_verified':False,'lifecycle_accepted':False},indent=2)+'\n',encoding='utf-8')
print('Staged exact-ticket/lease WDS insertion entry; startup caller still unbound')
