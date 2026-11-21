#!/usr/bin/env python3
"""Add checked configured-WDS loop; AP startup/first-open readiness unbound."""
import argparse,hashlib,json,shutil
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('source',type=Path);p.add_argument('output',type=Path)
a=p.parse_args();src=a.source.resolve(strict=True);out=a.output.resolve()
if out.exists() or src==out or src in out.parents or out in src.parents:p.error('new separate output required')
pins={'ap/ap_wds.c':'773738dd130e696682909188f894d274e7163a8f60f607b327b34ef675f584ad',
 'include/ap_wds.h':'9e4aeacc595eda48e3372f0c157c9868a2b268657af82e7ba6e94afd693875e1'}
texts={}
for n,h in pins.items():
 if hashlib.sha256((src/n).read_bytes()).hexdigest()!=h:p.error('unreviewed predecessor: '+n)
 texts[n]=(src/n).read_text()
def one(s,old,new):
 if s.count(old)!=1:p.error('unreviewed anchor: '+old)
 return s.replace(old,new,1)
s=texts['ap/ap_wds.c'];start=s.index('VOID AsicUpdateWdsRxWCIDTable(');end=s.index('\n}',start)+2
original=s[start:end]
body=one(original,'VOID AsicUpdateWdsRxWCIDTable(RTMP_ADAPTER *pAd)',
 'BOOLEAN wr_iot_wds_startup_table(RTMP_ADAPTER *pAd,const struct wr_iot_peer_open_ticket *ticket)')
body=one(body,'\tRT_802_11_WDS_ENTRY *wds_entry;', '''\tRT_802_11_WDS_ENTRY *wds_entry;
 BOOLEAN valid;
 if(!pAd||!ticket)return FALSE;
 NdisAcquireSpinLock(&pAd->MacTabLock);
 valid=wr_iot_peer_open_matches(&pAd->wr_iot_peer_open_owner,&pAd->wr_iot_peer_table_owner,ticket) &&
  pAd->wr_iot_peer_open_owner.phase==WR_PEER_OPEN_STARTUP;
 NdisReleaseSpinLock(&pAd->MacTabLock);
 if(!valid)return FALSE;''')
body=one(body,'pEntry = wr_iot_wds_insert_transaction(pAd, wds_entry->PeerWdsAddr, index, 2);',
 'pEntry = wr_iot_wds_insert_startup(pAd,wds_entry->PeerWdsAddr,index,ticket);')
body=one(body,'if (!pEntry) continue; /* Keep later configured links eligible. */',
 'if (!pEntry) return FALSE; /* Stop before reporting configured startup complete. */')
body=one(body,'\treturn;', ''' NdisAcquireSpinLock(&pAd->MacTabLock);
 valid=wr_iot_peer_open_matches(&pAd->wr_iot_peer_open_owner,&pAd->wr_iot_peer_table_owner,ticket) &&
  pAd->wr_iot_peer_open_owner.phase==WR_PEER_OPEN_STARTUP;
 NdisReleaseSpinLock(&pAd->MacTabLock);
 return valid;''')
texts['ap/ap_wds.c']=s[:end]+'\n\n'+body+s[end:]
texts['include/ap_wds.h']=one(texts['include/ap_wds.h'],'VOID AsicUpdateWdsRxWCIDTable(',
 '''BOOLEAN wr_iot_wds_startup_table(RTMP_ADAPTER *pAd,const struct wr_iot_peer_open_ticket *ticket);
VOID AsicUpdateWdsRxWCIDTable(''')
shutil.copytree(src,out)
for n,s in texts.items():(out/n).write_text(s,encoding='utf-8',newline='\n')
out.with_name(out.name+'-wds-startup-loop.json').write_text(json.dumps({
 'input_sha256':pins,'output_sha256':{n:hashlib.sha256((out/n).read_bytes()).hexdigest() for n in pins},
 'scope':'checked configured WDS loop; old generic loop preserved, APStartUp caller absent',
 'apstartup_caller_bound':False,'first_open_record_ready':False,
 'target_compiled':False,'runtime_verified':False,'lifecycle_accepted':False},indent=2)+'\n',encoding='utf-8')
print('Staged checked configured WDS loop; first-open record readiness unaccepted')
