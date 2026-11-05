#!/usr/bin/env python3
"""Prepare MCU-only software interrupt masks while hardware stays disabled."""
import argparse
import hashlib
import json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('--install-isolated',action='store_true',required=True);a=p.parse_args()
src=a.source.resolve();mp=Path(str(src)+'.manifest.json');raw=mp.read_bytes();manifest=json.loads(raw)
actual={str(f.relative_to(src)):hashlib.sha256(f.read_bytes()).hexdigest() for f in src.rglob('*') if f.is_file()}
if (manifest.get('production_installed') is not False or manifest.get('target_compiled') is not False or
    'mcu_boot_other_tx_idle' not in manifest or 'mcu_boot_irq_prepare' in manifest or actual!=manifest['merged_driver_sha256']):
 p.error('Expected unchanged isolated other-TX idle candidate')
names=('include/rtmp.h','include/mcu/andes_core.h','common/rtmp_init.c','mcu/andes_core.c')
changes={n:(src/n).read_text() for n in names}
def one(name,old,new):
 if changes[name].count(old)!=1:raise ValueError('Changed ring transaction anchor: '+name+': '+old)
 changes[name]=changes[name].replace(old,new)
one('include/rtmp.h','wr_iot_boot_ctrl_state,wr_iot_boot_rx_state;',
    'wr_iot_boot_ctrl_state,wr_iot_boot_rx_state,wr_iot_boot_irq_state;\n unsigned int wr_iot_boot_irq_saved_enable,wr_iot_boot_irq_saved_disable,wr_iot_boot_irq_saved_pending;')
one('common/rtmp_init.c','pAd->wr_iot_boot_ctrl_state=pAd->wr_iot_boot_rx_state=0;',
    'pAd->wr_iot_boot_ctrl_state=pAd->wr_iot_boot_rx_state=pAd->wr_iot_boot_irq_state=0;\n        pAd->wr_iot_boot_irq_saved_enable=pAd->wr_iot_boot_irq_saved_disable=pAd->wr_iot_boot_irq_saved_pending=0;')
one('include/rtmp.h','INT wr_iot_nettask_boot_rx_restart(RTMP_ADAPTER *pAd);',
    'INT wr_iot_nettask_boot_rx_restart(RTMP_ADAPTER *pAd);\nINT wr_iot_nettask_boot_irq_prepare(RTMP_ADAPTER *ad);')
one('include/mcu/andes_core.h','INT32 wr_iot_mcu_boot_rx_restart(struct _RTMP_ADAPTER *ad);',
    'INT32 wr_iot_mcu_boot_rx_restart(struct _RTMP_ADAPTER *ad);\nINT32 wr_iot_mcu_boot_irq_prepare_owned(struct _RTMP_ADAPTER *ad);\nINT32 wr_iot_mcu_boot_irq_prepare(struct _RTMP_ADAPTER *ad);')
one('mcu/andes_core.c','#include "wr-iot-mcu-boot-rx-restart.inc"',
    '#include "wr-iot-mcu-boot-rx-restart.inc"\n#include "wr-iot-mcu-boot-irq-owner.inc"')
name='os/linux/rt_rbus_pci_drv.c';text=(src/name).read_text();anchor='#include "wr-iot-mcu-nettask-bootstrap.inc"'
if text.count(anchor)!=1:raise ValueError('Unreviewed bootstrap nettask include')
changes[name]=text.replace(anchor,anchor+'\n#include "wr-iot-mcu-boot-irq-prepare.inc"')
for asset in ('mcu-boot-irq-prepare.inc','mcu-boot-irq-owner.inc'):
 changes['include/wr-iot-'+asset]=Path(__file__).with_name(asset).read_text()
for name,value in changes.items():(src/name).write_text(value)
hashes={n:hashlib.sha256((src/n).read_bytes()).hexdigest() for n in changes}
manifest['merged_driver_sha256'].update(hashes);manifest['candidate_driver_sha256'].update(hashes)
manifest['mcu_boot_irq_prepare']={'input_manifest_sha256':hashlib.sha256(raw).hexdigest(),'output_sha256':hashes,'scope':'narrow software IRQ preparation under irq/interrupt/lane locks; hardware masked, no DMA/epoch commit','target_compiled':False,'runtime_verified':False,'firmware_epoch_verified':False,'loader_bound':False}
mp.write_text(json.dumps(manifest,indent=2)+'\n')
