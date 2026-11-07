#!/usr/bin/env python3
"""Refuse unsafe bootstrap ASIC continuation/reload after firmware receipt."""
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
 'mcu_sys_scheduler' not in m or 'mcu_post_fw_init' in m or actual!=m['merged_driver_sha256']):
 p.error('Expected unchanged isolated MCU scheduler candidate')
name='common/rtmp_init.c';text=(src/name).read_text();start=text.index('NDIS_STATUS\tNICInitializeAdapter(');end=text.index('\nINT rtmp_hif_cyc_init(',start);body=text[start:end]
def one(old,new):
 global body
 if body.count(old)!=1:p.error('Changed post-firmware init anchor')
 body=body.replace(old,new)
guard='#if defined(MT7603) && defined(MT_MAC) && defined(RTMP_PCI_SUPPORT)'
one('\tUINT rty_cnt = 0;', '\tUINT rty_cnt = 0;\n'+guard+'''
 struct wr_iot_mcu_boot_ticket saved_boot;
 const struct wr_iot_mcu_boot_ticket *boot=NULL;
 if(pAd->wr_iot_boot_active){saved_boot=pAd->wr_iot_boot_ticket;boot=&saved_boot;}
#endif''')
abort=guard+'''
  if(boot){
   (void)wr_iot_mcu_boot_loader_abort(pAd,boot);
   return NDIS_STATUS_FAILURE;
  }
#endif
'''
one('\tif (AsicWaitPDMAIdle(pAd, 100, 1000) != TRUE) {',
 '\tif (AsicWaitPDMAIdle(pAd, 100, 1000) != TRUE) {\n'+abort)
one('\tif (NICInitializeAsic(pAd , bHardReset) != NDIS_STATUS_SUCCESS)\n\t{',
 '\tif (NICInitializeAsic(pAd , bHardReset) != NDIS_STATUS_SUCCESS)\n\t{\n'+abort)
one('\t\t\t\tNICLoadFirmware(pAd);',
 '\t\t\t\tif(NICLoadFirmware(pAd)!=NDIS_STATUS_SUCCESS)return NDIS_STATUS_FAILURE;')
(src/name).write_text(text[:start]+body+text[end:])
digest=hashlib.sha256((src/name).read_bytes()).hexdigest()
m['merged_driver_sha256'][name]=digest;m['candidate_driver_sha256'][name]=digest
m['mcu_post_fw_init']={'input_manifest_sha256':hashlib.sha256(raw).hexdigest(),
 'output_sha256':{name:digest},'normal_init_refusal_removed':False,
 'target_compiled':False,'runtime_verified':False}
mp.write_text(json.dumps(m,indent=2)+'\n')
