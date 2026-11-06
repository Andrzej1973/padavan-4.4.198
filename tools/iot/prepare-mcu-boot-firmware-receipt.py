#!/usr/bin/env python3
"""Record owned Method1 FW_START/RUN completion, without normal promotion."""
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
 'mcu_command_admission' not in m or 'mcu_boot_firmware_receipt' in m or actual!=m['merged_driver_sha256']):
 p.error('Expected unchanged isolated command-admission candidate')
changes={}
def one(name,old,new):
 text=changes.get(name,(src/name).read_text())
 if text.count(old)!=1:p.error('Changed firmware receipt anchor: '+name)
 changes[name]=text.replace(old,new)
one('include/rtmp.h','unsigned int wr_iot_control_users,wr_iot_control_poisoned;',
 'unsigned int wr_iot_control_users,wr_iot_control_poisoned;\n unsigned int wr_iot_boot_fw_state;\n unsigned long wr_iot_boot_fw_radio_serial,wr_iot_boot_fw_radio_epoch;')
one('common/rtmp_init.c','pAd->wr_iot_control_users=pAd->wr_iot_control_poisoned=0;',
 'pAd->wr_iot_control_users=pAd->wr_iot_control_poisoned=0;\n        pAd->wr_iot_boot_fw_state=0;\n        pAd->wr_iot_boot_fw_radio_serial=pAd->wr_iot_boot_fw_radio_epoch=0;')
one('mcu/andes_core.c','#include "wr-iot-mcu-boot-thaw.inc"',
 '#include "wr-iot-mcu-boot-thaw.inc"\n#include "wr-iot-mcu-boot-firmware-receipt.inc"')
anchor='INT32 wr_iot_mcu_boot_thaw(struct _RTMP_ADAPTER *ad,const struct wr_iot_mcu_boot_ticket *ticket);'
one('include/mcu/andes_core.h',anchor,anchor+'\nINT32 wr_iot_mcu_boot_firmware_receipt(struct _RTMP_ADAPTER *ad,const struct wr_iot_mcu_boot_ticket *ticket);')
name='mcu/andes_mt.c';text=(src/name).read_text();start=text.index('static NDIS_STATUS AndesMTLoadFwMethod1(');end=text.index('static NDIS_STATUS AndesMTLoadFwMethod2(',start)
body=text[start:end];anchor='\telse\n\t{\n\t\tCtl->Stage = FW_RUN_TIME;\n\t}\n\ndone:'
if body.count(anchor)!=1:p.error('Changed Method1 successful RUN completion')
body=body.replace(anchor,anchor.replace('\n\ndone:', '''
#if defined(MT_MAC) && defined(RTMP_PCI_SUPPORT)
 if(boot&&!ret){
  ret=wr_iot_mcu_boot_firmware_receipt(ad,boot);
  if(ret)goto done;
 }
#endif

done:'''))
changes[name]=text[:start]+body+text[end:]
name='include/wr-iot-mcu-boot-scheduler-owner.inc';text=(src/name).read_text()
anchor='ad->MCUCtrl.Stage==FW_RUN_TIME'
if text.count(anchor)!=3:p.error('Changed scheduler receipt gates')
changes[name]=text.replace(anchor,'''ad->wr_iot_boot_fw_state==2&&
       ad->wr_iot_boot_fw_radio_serial==ad->wr_iot_boot_ticket.radio_serial&&
       ad->wr_iot_boot_fw_radio_epoch==ad->wr_iot_boot_ticket.radio_epoch&&
       '''+anchor)
anchor='!ad->wr_iot_boot_scheduler_state&&!ad->wr_iot_boot_frozen&&'
if changes[name].count(anchor)!=1:p.error('Changed scheduler constructor handover')
changes[name]=changes[name].replace(anchor,
 '!ad->wr_iot_boot_scheduler_state&&ad->wr_iot_boot_frozen&&')
changes['include/wr-iot-mcu-boot-firmware-receipt.inc']=Path(__file__).with_name('mcu-boot-firmware-receipt.inc').read_text()
for name,text in changes.items():(src/name).write_text(text)
hashes={name:hashlib.sha256((src/name).read_bytes()).hexdigest() for name in changes}
m['merged_driver_sha256'].update(hashes);m['candidate_driver_sha256'].update(hashes)
m['mcu_boot_firmware_receipt']={'input_manifest_sha256':hashlib.sha256(raw).hexdigest(),
 'output_sha256':hashes,'scheduler_bound':False,'normal_admission':False,
 'target_compiled':False,'runtime_verified':False}
mp.write_text(json.dumps(m,indent=2)+'\n')
