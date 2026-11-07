#!/usr/bin/env python3
"""Connect isolated MCUSysInit scheduler result; keep outer boot-init refusal."""
import argparse
import hashlib
import json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path)
p.add_argument('--install-isolated',action='store_true',required=True)
a=p.parse_args();src=a.source.resolve();mp=Path(str(src)+'.manifest.json')
raw=mp.read_bytes();m=json.loads(raw)
actual={str(f.relative_to(src)):hashlib.sha256(f.read_bytes()).hexdigest() for f in src.rglob('*') if f.is_file()}
if (m.get('production_installed') is not False or m.get('target_compiled') is not False or
 'mcu_boot_firmware_receipt' not in m or 'mcu_sys_scheduler' in m or actual!=m['merged_driver_sha256']):
 p.error('Expected unchanged isolated firmware-receipt candidate')
name='mcu/mcu.c';text=(src/name).read_text();start=text.index('INT32 MCUSysInit(RTMP_ADAPTER *pAd)');end=text.index('INT32 MCUSysExit(',start)
body=text[start:end]
def one(old,new):
 global body
 if body.count(old)!=1:p.error('Changed MCUSysInit scheduler anchor')
 body=body.replace(old,new)
guard='#if defined(MT7603) && defined(MT_MAC) && defined(RTMP_PCI_SUPPORT)'
one('\tINT32 Ret = 0;', '\tINT32 Ret = 0;\n'+guard+'''
 struct wr_iot_mcu_boot_ticket saved_boot;
 const struct wr_iot_mcu_boot_ticket *boot=NULL;
 if(pAd->wr_iot_boot_active){saved_boot=pAd->wr_iot_boot_ticket;boot=&saved_boot;}
#endif''')
anchor='\t\treturn -1;'
one(anchor,guard+'''
  if(boot)(void)wr_iot_mcu_boot_loader_abort(pAd,boot);
#endif
'''+anchor)
anchor='\n#ifdef MT_MAC\n\tif (pAd->chipCap.hif_type == HIF_MT) {'
one(anchor,'\n'+guard+'''
 if(boot){
  Ret=wr_iot_mcu_boot_scheduler_run(pAd,boot);
  if(Ret!=NDIS_STATUS_SUCCESS){
   (void)wr_iot_mcu_boot_loader_abort(pAd,boot);
   return -1;
  }
  return NDIS_STATUS_SUCCESS;
 }
#endif
'''+anchor)
one('\t\tAsicDMASchedulerInit(pAd, DMA_SCH_LMAC);',
 '\t\tif(AsicDMASchedulerInit(pAd, DMA_SCH_LMAC)!=TRUE)return -1;')
(src/name).write_text(text[:start]+body+text[end:])
digest=hashlib.sha256((src/name).read_bytes()).hexdigest()
m['merged_driver_sha256'][name]=digest;m['candidate_driver_sha256'][name]=digest
m['mcu_sys_scheduler']={'input_manifest_sha256':hashlib.sha256(raw).hexdigest(),
 'output_sha256':{name:digest},'isolated_scheduler_invocation':True,
 'normal_init_refusal_removed':False,'all_remap_users_verified':False,
 'target_compiled':False,'runtime_verified':False}
mp.write_text(json.dumps(m,indent=2)+'\n')
