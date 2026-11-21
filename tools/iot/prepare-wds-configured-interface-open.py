#!/usr/bin/env python3
"""Complete configured peers on exact WDS interface open, not main startup wait."""
import argparse,hashlib,json,shutil
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('source',type=Path);p.add_argument('output',type=Path)
a=p.parse_args();src=a.source.resolve(strict=True);out=a.output.resolve()
if out.exists() or src==out or src in out.parents or out in src.parents:p.error('new separate output required')
pins={'ap/ap_wds.c':'bfe68aba15f5fca95a6d29503b85fefba719a03ccb08f7a5b54a167fc6bf3449',
 'ap/ap_wds_inf.c':'a378d9ce362f7c68c524aa145411f9c802906256d681b1ae17b19fb9c4fa6d33',
 'include/rtmp.h':'990dd1ef28069d745be154222e7bf0edf009321bc116c41785d9b749abd26170'}
texts={}
for n,h in pins.items():
 if hashlib.sha256((src/n).read_bytes()).hexdigest()!=h:p.error('unreviewed predecessor: '+n)
 texts[n]=(src/n).read_text()
def one(s,old,new):
 if s.count(old)!=1:p.error('unreviewed anchor: '+old)
 return s.replace(old,new,1)
s=texts['ap/ap_wds.c'];start=s.index('static MAC_TABLE_ENTRY *wr_iot_wds_insert_transaction_owned(');end=s.index('\n}',start)+2;body=s[start:end]
body=one(body,'wr_iot_wds_insert_transaction_owned(', 'wr_iot_wds_insert_transaction_identity(')
body=one(body,'unsigned long wr_open_lease)', 'unsigned long wr_open_lease,PNET_DEV expected_device,unsigned long expected_generation)')
body=one(body,'if (device && !pAd->wr_iot_transition.retiring &&',
 'if (device && (!expected_device || device==expected_device) && !pAd->wr_iot_transition.retiring &&')
body=one(body,'if (r->device == device && r->published && !r->removing &&',
 'if (r->device == device && (!expected_device || r->generation==expected_generation) && r->published && !r->removing &&')
wrapper='''
static MAC_TABLE_ENTRY *wr_iot_wds_insert_transaction_owned(RTMP_ADAPTER *pAd,UCHAR *addr,
 UINT index,UINT mode,const struct wr_iot_peer_open_ticket *ticket,unsigned long lease)
{
 return wr_iot_wds_insert_transaction_identity(pAd,addr,index,mode,ticket,lease,NULL,0);
}
#include "wr-iot-wds-configured-interface-open.inc"
'''
texts['ap/ap_wds.c']=s[:start]+body+wrapper+s[end:]
s=texts['ap/ap_wds_inf.c'];start=s.index('INT WdsVirtualIF_open(');end=s.index('\n}',start)+2;body=s[start:end]
body=one(body,'if(!owned)return -1;',
 '''if(!owned)return -1;
 /* This interface, not main startup, now owns configured-peer completion.
  * Failed ndo_open retains its uncertain owned record/module pin for recovery. */
 if(!wr_iot_wds_configured_interface_open(adapter,dev,generation))return -1;''')
texts['ap/ap_wds_inf.c']=s[:start]+body+s[end:]
texts['include/rtmp.h']=one(texts['include/rtmp.h'],'MAC_TABLE_ENTRY *wr_iot_wds_insert_startup(',
 '''BOOLEAN wr_iot_wds_configured_interface_open(RTMP_ADAPTER *pAd,PNET_DEV device,unsigned long generation);
MAC_TABLE_ENTRY *wr_iot_wds_insert_startup(''')
shutil.copytree(src,out)
for n,s in texts.items():(out/n).write_text(s,encoding='utf-8',newline='\n')
shutil.copyfile(Path(__file__).with_name('wds-configured-interface-open.inc'),out/'include/wr-iot-wds-configured-interface-open.inc')
out.with_name(out.name+'-configured-interface-open.json').write_text(json.dumps({
 'input_sha256':pins,'output_sha256':{n:hashlib.sha256((out/n).read_bytes()).hexdigest() for n in pins},
 'scope':'configured peer completion after exact WDS interface open; failure recovery unbound',
 'main_open_waits_for_closed_wds':False,'failed_wds_open_recovery_bound':False,
 'target_compiled':False,'runtime_verified':False,'lifecycle_accepted':False},indent=2)+'\n',encoding='utf-8')
print('Staged configured WDS completion after exact interface ownership')
