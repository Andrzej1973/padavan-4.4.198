#!/usr/bin/env python3
"""Install isolated private EDCA register route with shared timing ownership."""
import argparse
import hashlib
import json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('source',type=Path)
p.add_argument('--install-isolated',action='store_true',required=True)
a=p.parse_args();src=a.source.resolve();mp=Path(str(src)+'.manifest.json')
raw=mp.read_bytes();m=json.loads(raw)
actual={str(f.relative_to(src)):hashlib.sha256(f.read_bytes()).hexdigest() for f in src.rglob('*') if f.is_file()}
if (m.get('production_installed') is not False or m.get('target_compiled') is not False or
 'mcu_config_slot_direct' not in m or 'mcu_config_edca_direct' in m or actual!=m['merged_driver_sha256']):
 p.error('Expected unchanged isolated direct-slot candidate')
changes={}
def one(name,old,new):
 text=changes.get(name,(src/name).read_text())
 if text.count(old)!=1:p.error('Changed direct EDCA anchor: '+name)
 changes[name]=text.replace(old,new,1)
anchor='#include "wr-iot-mcu-config-slot-owner.inc"'
one('mcu/andes_core.c',anchor,anchor+'\n#include "mcu-config-edca-plan.h"\n#include "wr-iot-mcu-config-edca-mmio.inc"\n#include "wr-iot-mcu-config-edca-owner.inc"')
anchor='INT32 wr_iot_mcu_config_fail(struct _RTMP_ADAPTER *ad);'
one('include/mcu/andes_core.h',anchor,anchor+'\nINT32 wr_iot_mcu_config_edca_owned(struct _RTMP_ADAPTER *ad,const struct wr_iot_mcu_boot_ticket *ticket,const unsigned char *data,unsigned int length);')
name='mcu/andes_mt.c';text=(src/name).read_text()
start=text.index('INT32 CmdEdcaParameterSet(');end=text.index('\n}\n',start)+3
body=text[start:end];anchor='\tsize = 4+sizeof(TX_AC_PARAM_T)*EdcaParam.ucTotalNum;'
if body.count(anchor)!=1:p.error('Changed EDCA size boundary')
body=body.replace(anchor,anchor+'''
#if defined(MT7603) && defined(MT_MAC) && defined(RTMP_PCI_SUPPORT)
 if(pAd->wr_iot_boot_active){
  if(wr_iot_mcu_config_edca_owned(pAd,&pAd->wr_iot_boot_ticket,
     (const unsigned char *)&EdcaParam,size)!=NDIS_STATUS_SUCCESS)
   return wr_iot_mcu_config_fail(pAd);
  return NDIS_STATUS_SUCCESS;
 }
#endif
''',1)
changes[name]=text[:start]+body+text[end:]
for target,local in [('wr-iot-mcu-config-slot-owner.inc','mcu-config-slot-owner.inc'),
 ('mcu-config-edca-plan.h','mcu-config-edca-plan.h'),
 ('wr-iot-mcu-config-edca-mmio.inc','mcu-config-edca-mmio.inc'),
 ('wr-iot-mcu-config-edca-owner.inc','mcu-config-edca-owner.inc')]:
 changes['include/'+target]=Path(__file__).with_name(local).read_text()
for name,text in changes.items():(src/name).write_text(text)
hashes={name:hashlib.sha256((src/name).read_bytes()).hexdigest() for name in changes}
m['merged_driver_sha256'].update(hashes);m['candidate_driver_sha256'].update(hashes)
m['mcu_config_edca_direct']={'input_manifest_sha256':hashlib.sha256(raw).hexdigest(),
 'output_sha256':hashes,'private_edca_firmware_tx':False,'target_compiled':False,'runtime_verified':False}
mp.write_text(json.dumps(m,indent=2)+'\n')
