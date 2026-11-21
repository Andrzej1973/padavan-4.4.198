#!/usr/bin/env python3
"""Install frozen scheduler lease without enabling MCUSysInit admission."""
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
if (m.get('production_installed') is not False or m.get('target_compiled') is not False
 or 'mcu_boot_scheduler' not in m or 'mcu_boot_scheduler_owner' in m or actual!=m['merged_driver_sha256']):
 p.error('Expected unchanged isolated scheduler candidate')
changes={}
edits=(
 ('include/rtmp.h','unsigned int wr_iot_boot_epoch_done,wr_iot_boot_epoch_retired_mask;',
  'unsigned int wr_iot_boot_epoch_done,wr_iot_boot_epoch_retired_mask;\n unsigned int wr_iot_boot_scheduler_state;'),
 ('common/rtmp_init.c','pAd->wr_iot_boot_epoch_done=pAd->wr_iot_boot_epoch_retired_mask=0;',
  'pAd->wr_iot_boot_epoch_done=pAd->wr_iot_boot_epoch_retired_mask=0;\n        pAd->wr_iot_boot_scheduler_state=0;'),
 ('mcu/andes_core.c','#include "wr-iot-mcu-boot-loader-abort.inc"',
  '#include "wr-iot-mcu-boot-loader-abort.inc"\n#include "wr-iot-mcu-boot-scheduler-owner.inc"'),
 ('include/mcu/andes_core.h','INT32 wr_iot_mcu_boot_thaw(struct _RTMP_ADAPTER *ad,const struct wr_iot_mcu_boot_ticket *ticket);',
  'INT32 wr_iot_mcu_boot_thaw(struct _RTMP_ADAPTER *ad,const struct wr_iot_mcu_boot_ticket *ticket);\nINT32 wr_iot_mcu_boot_scheduler_claim(struct _RTMP_ADAPTER *ad,const struct wr_iot_mcu_boot_ticket *ticket);\nINT32 wr_iot_mcu_boot_scheduler_finish(struct _RTMP_ADAPTER *ad,const struct wr_iot_mcu_boot_ticket *ticket,int success);'))
for name,old,new in edits:
 text=(src/name).read_text()
 if text.count(old)!=1:p.error('Changed scheduler owner anchor: '+name)
 changes[name]=text.replace(old,new)
changes['include/wr-iot-mcu-boot-scheduler-owner.inc']=Path(__file__).with_name('mcu-boot-scheduler-owner.inc').read_text()
name='include/mcu/andes_core.h'
anchor='INT32 wr_iot_mcu_boot_scheduler_claim(struct _RTMP_ADAPTER *ad,const struct wr_iot_mcu_boot_ticket *ticket);'
changes[name]=changes[name].replace(anchor,anchor+
 '\nINT32 wr_iot_mcu_boot_scheduler_owned(struct _RTMP_ADAPTER *ad);'+
 '\nINT32 wr_iot_mcu_boot_scheduler_run(struct _RTMP_ADAPTER *ad,const struct wr_iot_mcu_boot_ticket *ticket);')
name='include/wr-iot-mcu-boot-scheduler.inc';text=(src/name).read_text()
if text.count('wr_iot_mcu_boot_owned(ad)')!=2:p.error('Changed scheduler ownership gates')
text=text.replace('wr_iot_mcu_boot_owned(ad)','wr_iot_mcu_boot_scheduler_owned(ad)')
text=text.replace('ad->wr_iot_boot_frozen||','!ad->wr_iot_boot_frozen||')
changes[name]=text
for name,text in changes.items():(src/name).write_text(text)
hashes={name:hashlib.sha256((src/name).read_bytes()).hexdigest() for name in changes}
m['merged_driver_sha256'].update(hashes);m['candidate_driver_sha256'].update(hashes)
m['mcu_boot_scheduler_owner']={'input_manifest_sha256':hashlib.sha256(raw).hexdigest(),'output_sha256':hashes,
 'bound':False,'target_compiled':False,'runtime_verified':False}
mp.write_text(json.dumps(m,indent=2)+'\n')
