#!/usr/bin/env python3
"""Pass exact startup ticket/lease through WDS; outer APStartUp not yet bound."""
import argparse,hashlib,json,shutil
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('source',type=Path);p.add_argument('output',type=Path)
a=p.parse_args();src=a.source.resolve(strict=True);out=a.output.resolve()
if out.exists() or src==out or src in out.parents or out in src.parents:p.error('new separate output required')
pins={'ap/ap_wds.c':'ef7ff6ed2cf5c53e0ba1b5fd2dca0401315b0011f543fe204028ae555d9fd1a8',
 'include/rtmp.h':'3b438be8e42123238d6e04162680989613268c2b2b39b9afd5900e1d0213e21a'}
texts={}
for n,h in pins.items():
 if hashlib.sha256((src/n).read_bytes()).hexdigest()!=h:p.error('unreviewed predecessor: '+n)
 texts[n]=(src/n).read_text()
def one(s,old,new):
 if s.count(old)!=1:p.error('unreviewed anchor: '+old)
 return s.replace(old,new,1)
s=texts['ap/ap_wds.c'];start=s.index('static MAC_TABLE_ENTRY *wr_iot_wds_insert_body(');end=s.index('\n}',start)+2;body=s[start:end]
body=one(body,'UINT WdsTabIdx)', 'UINT WdsTabIdx,const struct wr_iot_peer_open_ticket *wr_open_ticket,unsigned long wr_open_lease)')
body=one(body,'pEntry = MacTableInsertEntry(pAd, pAddr, wdev, ENTRY_WDS, OPMODE_AP, TRUE);',
 '''if(wr_open_ticket)
   pEntry = wr_iot_mac_insert_startup_wds(pAd,pAddr,wdev,wr_open_ticket,wr_open_lease);
  else
   pEntry = MacTableInsertEntry(pAd, pAddr, wdev, ENTRY_WDS, OPMODE_AP, TRUE);''')
s=s[:start]+body+s[end:]
start=s.index('static MAC_TABLE_ENTRY *wr_iot_wds_insert_transaction(');end=s.index('\n}',start)+2;body=s[start:end]
body=one(body,'wr_iot_wds_insert_transaction(', 'wr_iot_wds_insert_transaction_owned(')
body=one(body,'UINT finish_mode)', 'UINT finish_mode,const struct wr_iot_peer_open_ticket *wr_open_ticket,unsigned long wr_open_lease)')
body=one(body,'wr_iot_wds_insert_body(pAd, pAddr, WdsTabIdx)',
 'wr_iot_wds_insert_body(pAd, pAddr, WdsTabIdx,wr_open_ticket,wr_open_lease)')
wrapper='''
static MAC_TABLE_ENTRY *wr_iot_wds_insert_transaction(RTMP_ADAPTER *pAd,UCHAR *pAddr,UINT index,UINT mode)
{
 return wr_iot_wds_insert_transaction_owned(pAd,pAddr,index,mode,NULL,0);
}
#include "wr-iot-wds-startup-transaction.inc"
'''
s=s[:start]+body+wrapper+s[end:];texts['ap/ap_wds.c']=s
texts['include/rtmp.h']=one(texts['include/rtmp.h'],'MAC_TABLE_ENTRY *wr_iot_mac_insert_startup_wds(',
 '''MAC_TABLE_ENTRY *wr_iot_wds_insert_startup(RTMP_ADAPTER *pAd,UCHAR *pAddr,
 UINT index,const struct wr_iot_peer_open_ticket *ticket);
MAC_TABLE_ENTRY *wr_iot_mac_insert_startup_wds(''')
shutil.copytree(src,out)
for n,s in texts.items():(out/n).write_text(s,encoding='utf-8',newline='\n')
shutil.copyfile(Path(__file__).with_name('wds-startup-transaction.inc'),out/'include/wr-iot-wds-startup-transaction.inc')
out.with_name(out.name+'-wds-startup-transaction.json').write_text(json.dumps({
 'input_sha256':pins,'output_sha256':{n:hashlib.sha256((out/n).read_bytes()).hexdigest() for n in pins},
 'scope':'explicit startup entry into counted WDS transaction; APStartUp and outer open still absent',
 'apstartup_caller_bound':False,'target_compiled':False,'runtime_verified':False,'lifecycle_accepted':False},indent=2)+'\n',encoding='utf-8')
print('Staged WDS ticket/lease path and whole transaction lease completion')
