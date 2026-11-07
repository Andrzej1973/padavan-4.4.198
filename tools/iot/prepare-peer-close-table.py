#!/usr/bin/env python3
"""Hold table through close teardown/clear, seal on completed software close."""
import argparse,hashlib,json,shutil
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('source',type=Path);p.add_argument('output',type=Path)
a=p.parse_args();src=a.source.resolve(strict=True);out=a.output.resolve()
if out.exists() or src==out or src in out.parents or out in src.parents:p.error('new separate output required')
pins={'common/rtmp_init_inf.c':'1473ea6418c1c2454e5947b4d2839c6430640217e825743f99e1bf20a7006d47',
 'common/rtmp_init.c':'f387a500cc227eb94377549a90fcd73c35020e9cb2523c69aaf34bd80e55f1ab',
 'include/rtmp.h':'d9bfe321cbf2844f7303e67b1121a7ec9daed4a14a37424d6d108e738748cb3d'}
texts={}
for n,h in pins.items():
 if hashlib.sha256((src/n).read_bytes()).hexdigest()!=h:p.error('unreviewed predecessor: '+n)
 texts[n]=(src/n).read_text()
def one(s,old,new):
 if s.count(old)!=1:p.error('unreviewed anchor: '+old)
 return s.replace(old,new,1)
texts['include/rtmp.h']=one(texts['include/rtmp.h'],'struct wr_iot_peer_table_owner wr_iot_peer_table_owner;',
 'struct wr_iot_peer_table_owner wr_iot_peer_table_owner;\n unsigned long wr_iot_peer_close_serial;')
texts['common/rtmp_init.c']=one(texts['common/rtmp_init.c'],'wr_iot_peer_table_owner_init(&pAd->wr_iot_peer_table_owner);',
 'wr_iot_peer_table_owner_init(&pAd->wr_iot_peer_table_owner);\n\t\tpAd->wr_iot_peer_close_serial=0;')
s=texts['common/rtmp_init_inf.c'];s=one(s,'INT RTMPDrvClose(', '#include "wr-iot-peer-close-table.inc"\n\nINT RTMPDrvClose(')
for signature in ['INT RTMPDrvClose(', 'INT wr_iot_drv_close_checked(']:
 start=s.index(signature);end=s.index('\n}',start)+2;body=s[start:end]
 body=one(body,'\t/* Close net tasklets*/',
 ''' if(!wr_iot_peer_close_hold(pAd))return NDIS_STATUS_FAILURE;
\t/* Close net tasklets*/''')
 body=one(body,'NdisZeroMemory(&pAd->MacTab, sizeof(MAC_TABLE));',
 'if(!wr_iot_peer_close_clear(pAd))return NDIS_STATUS_FAILURE;')
 if signature=='INT RTMPDrvClose(':
  body=one(body,'return NDIS_STATUS_SUCCESS;',
   'if(!wr_iot_peer_close_finish(pAd))return NDIS_STATUS_FAILURE;\n\treturn NDIS_STATUS_SUCCESS;')
 else:
  body=one(body,' if(!wr_iot_peer_close_hold(pAd))return NDIS_STATUS_FAILURE;',
   ''' if(!wr_iot_peer_close_hold(pAd)){
  /* APShutdown already ran: never replay destructive stage zero. */
  RTMP_IRQ_LOCK(&pAd->wr_iot_transition_lock,flags);
  pAd->wr_iot_transition.shutdown_stage=3U;
  RTMP_IRQ_UNLOCK(&pAd->wr_iot_transition_lock,flags);
  return NDIS_STATUS_FAILURE;
 }''')
  anchor=' RTMP_IRQ_LOCK(&pAd->wr_iot_transition_lock,flags);\n pAd->wr_iot_transition.shutdown_stage=2U;'
  body=one(body,anchor,' if(!wr_iot_peer_close_finish(pAd))return NDIS_STATUS_FAILURE;\n'+anchor)
 s=s[:start]+body+s[end:]
texts['common/rtmp_init_inf.c']=s
shutil.copytree(src,out)
for n,s in texts.items():(out/n).write_text(s,encoding='utf-8',newline='\n')
for n,target in [('peer-close-table.inc','wr-iot-peer-close-table.inc'),('peer-table-owner.h','peer-table-owner.h'),('peer-open-owner.h','peer-open-owner.h')]:
 shutil.copyfile(Path(__file__).with_name(n),out/'include'/target)
out.with_name(out.name+'-peer-close-table.json').write_text(json.dumps({
 'input_sha256':pins,'output_sha256':{n:hashlib.sha256((out/n).read_bytes()).hexdigest() for n in pins},
 'scope':'software close table hold/clear/seal; actual adapter free/DMA lifetime unproved',
 'target_compiled':False,'runtime_verified':False,'lifecycle_accepted':False,'adapter_free_guard_bound':False},indent=2)+'\n',encoding='utf-8')
print('Staged close table reservation, guarded full clear and completed-close seal')
