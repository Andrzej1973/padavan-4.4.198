#!/usr/bin/env python3
"""Stage task-pinned configuration owner, leaving command/data admission closed."""
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
 'mcu_post_fw_init' not in m or 'mcu_boot_config_owner' in m or actual!=m['merged_driver_sha256']):
 p.error('Expected unchanged isolated post-firmware candidate')
changes={}
def one(name,old,new):
 text=changes.get(name,(src/name).read_text())
 if text.count(old)!=1:p.error('Changed config owner anchor: '+name)
 changes[name]=text.replace(old,new)
one('include/rtmp.h','unsigned int wr_iot_boot_fw_state;',
 'unsigned int wr_iot_boot_fw_state;\n unsigned int wr_iot_boot_config_state;\n struct task_struct *wr_iot_boot_config_task;')
one('common/rtmp_init.c','pAd->wr_iot_boot_fw_state=0;',
 'pAd->wr_iot_boot_fw_state=0;\n        pAd->wr_iot_boot_config_state=0;pAd->wr_iot_boot_config_task=NULL;')
one('mcu/andes_core.c','#include "wr-iot-mcu-boot-firmware-receipt.inc"',
 '#include "wr-iot-mcu-boot-firmware-receipt.inc"\n#include <linux/sched.h>\n#include "wr-iot-mcu-boot-config-owner.inc"')
anchor='INT32 wr_iot_mcu_boot_firmware_receipt(struct _RTMP_ADAPTER *ad,const struct wr_iot_mcu_boot_ticket *ticket);'
one('include/mcu/andes_core.h',anchor,anchor+'\nINT32 wr_iot_mcu_boot_config_begin(struct _RTMP_ADAPTER *ad,const struct wr_iot_mcu_boot_ticket *ticket);\nINT32 wr_iot_mcu_boot_config_finish(struct _RTMP_ADAPTER *ad,const struct wr_iot_mcu_boot_ticket *ticket,int success);')
changes['include/wr-iot-mcu-boot-config-owner.inc']=Path(__file__).with_name('mcu-boot-config-owner.inc').read_text()
for name,text in changes.items():(src/name).write_text(text)
hashes={name:hashlib.sha256((src/name).read_bytes()).hexdigest() for name in changes}
m['merged_driver_sha256'].update(hashes);m['candidate_driver_sha256'].update(hashes)
m['mcu_boot_config_owner']={'input_manifest_sha256':hashlib.sha256(raw).hexdigest(),
 'output_sha256':hashes,'bound':False,'command_admission':False,
 'target_compiled':False,'runtime_verified':False}
mp.write_text(json.dumps(m,indent=2)+'\n')
