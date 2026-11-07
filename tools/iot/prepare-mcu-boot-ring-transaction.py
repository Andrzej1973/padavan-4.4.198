#!/usr/bin/env python3
"""Compose owned ROM/RX/control/ring transaction; sequence epoch commit remains unfinished."""
import argparse
import hashlib
import json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('--install-isolated',action='store_true',required=True);a=p.parse_args()
src=a.source.resolve();mp=Path(str(src)+'.manifest.json');raw=mp.read_bytes();manifest=json.loads(raw)
actual={str(f.relative_to(src)):hashlib.sha256(f.read_bytes()).hexdigest() for f in src.rglob('*') if f.is_file()}
if (manifest.get('production_installed') is not False or manifest.get('target_compiled') is not False or
    'mcu_boot_ring_rearm' not in manifest or 'mcu_boot_ring_transaction' in manifest or actual!=manifest['merged_driver_sha256']):
 p.error('Expected unchanged isolated ring rearm candidate')
names=('include/rtmp.h','include/mcu/andes_core.h','common/rtmp_init.c','mcu/andes_core.c')
changes={n:(src/n).read_text() for n in names}
def one(name,old,new):
 if changes[name].count(old)!=1:raise ValueError('Changed ring transaction anchor: '+name+': '+old)
 changes[name]=changes[name].replace(old,new)
one('include/rtmp.h','unsigned int wr_iot_boot_active,wr_iot_boot_failed,wr_iot_boot_mcu_only,wr_iot_boot_frozen;',
    'unsigned int wr_iot_boot_active,wr_iot_boot_failed,wr_iot_boot_mcu_only,wr_iot_boot_frozen;\n unsigned int wr_iot_boot_ring_stage,wr_iot_boot_ring_busy,wr_iot_boot_ring_failed;')
one('common/rtmp_init.c','pAd->wr_iot_boot_active=pAd->wr_iot_boot_failed=pAd->wr_iot_boot_mcu_only=pAd->wr_iot_boot_frozen=0;',
    'pAd->wr_iot_boot_active=pAd->wr_iot_boot_failed=pAd->wr_iot_boot_mcu_only=pAd->wr_iot_boot_frozen=0;\n        pAd->wr_iot_boot_ring_stage=pAd->wr_iot_boot_ring_busy=pAd->wr_iot_boot_ring_failed=0;')
one('mcu/andes_core.c','#include "wr-iot-mcu-boot-transport.inc"',
    '#include "wr-iot-mcu-boot-transport.inc"\n#include "wr-iot-mcu-boot-ring-transaction.inc"')
one('include/mcu/andes_core.h','INT32 wr_iot_mcu_boot_frozen_owned(struct _RTMP_ADAPTER *ad);',
    'INT32 wr_iot_mcu_boot_frozen_owned(struct _RTMP_ADAPTER *ad);\nINT32 wr_iot_mcu_boot_ring_transaction(struct _RTMP_ADAPTER *ad,const struct wr_iot_mcu_boot_ticket *ticket);')
changes['include/wr-iot-mcu-boot-ring-transaction.inc']=Path(__file__).with_name('mcu-boot-ring-transaction.inc').read_text()
for name,value in changes.items():(src/name).write_text(value)
hashes={n:hashlib.sha256((src/n).read_bytes()).hexdigest() for n in changes}
manifest['merged_driver_sha256'].update(hashes);manifest['candidate_driver_sha256'].update(hashes)
manifest['mcu_boot_ring_transaction']={'input_manifest_sha256':hashlib.sha256(raw).hexdigest(),'output_sha256':hashes,'scope':'owned four-stage ROM/RX/control/ring transaction with sticky failure; no sequence epoch commit or loader binding','target_compiled':False,'runtime_verified':False,'firmware_epoch_verified':False,'loader_bound':False}
mp.write_text(json.dumps(manifest,indent=2)+'\n')
