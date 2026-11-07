#!/usr/bin/env python3
"""Prepare MCU-only IRQ release and abort with constructors still frozen."""
import argparse
import hashlib
import json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('--install-isolated',action='store_true',required=True);a=p.parse_args()
src=a.source.resolve();mp=Path(str(src)+'.manifest.json');raw=mp.read_bytes();manifest=json.loads(raw)
actual={str(f.relative_to(src)):hashlib.sha256(f.read_bytes()).hexdigest() for f in src.rglob('*') if f.is_file()}
if (manifest.get('production_installed') is not False or manifest.get('target_compiled') is not False or
    'mcu_boot_irq_filter' not in manifest or 'mcu_boot_irq_unmask' in manifest or actual!=manifest['merged_driver_sha256']):
 p.error('Expected unchanged isolated bootstrap ISR filter candidate')
names=('include/rtmp.h','include/mcu/andes_core.h','common/rtmp_init.c','mcu/andes_core.c')
changes={n:(src/n).read_text() for n in names}
def one(name,old,new):
 if changes[name].count(old)!=1:raise ValueError('Changed ring transaction anchor: '+name+': '+old)
 changes[name]=changes[name].replace(old,new)
one('include/rtmp.h','wr_iot_boot_dma_saved_valid,wr_iot_boot_dma_stop_verified;',
    'wr_iot_boot_dma_saved_valid,wr_iot_boot_dma_stop_verified;\n unsigned int wr_iot_boot_irq_unmask_state,wr_iot_boot_irq_startup_owned;')
one('common/rtmp_init.c','pAd->wr_iot_boot_dma_saved_valid=pAd->wr_iot_boot_dma_stop_verified=0;',
    'pAd->wr_iot_boot_dma_saved_valid=pAd->wr_iot_boot_dma_stop_verified=0;\n        pAd->wr_iot_boot_irq_unmask_state=pAd->wr_iot_boot_irq_startup_owned=0;')
one('include/rtmp.h','INT wr_iot_nettask_boot_irq_prepare(RTMP_ADAPTER *ad);',
    'INT wr_iot_nettask_boot_irq_prepare(RTMP_ADAPTER *ad);\nINT wr_iot_nettask_boot_irq_unmask(RTMP_ADAPTER *ad);\nINT wr_iot_nettask_boot_irq_abort(RTMP_ADAPTER *ad);')
one('include/mcu/andes_core.h','INT32 wr_iot_mcu_boot_dma_start(struct _RTMP_ADAPTER *ad);',
    'INT32 wr_iot_mcu_boot_dma_start(struct _RTMP_ADAPTER *ad);\nINT32 wr_iot_mcu_boot_irq_unmask_owned(struct _RTMP_ADAPTER *ad);\nINT32 wr_iot_mcu_boot_irq_unmask(struct _RTMP_ADAPTER *ad);')
one('mcu/andes_core.c','#include "wr-iot-mcu-boot-dma-owner.inc"',
    '#include "wr-iot-mcu-boot-dma-owner.inc"\n#include "wr-iot-mcu-boot-irq-unmask-owner.inc"')
name='os/linux/rt_rbus_pci_drv.c';text=(src/name).read_text();anchor='#include "wr-iot-mcu-boot-irq-prepare.inc"'
if text.count(anchor)!=1:raise ValueError('Unreviewed IRQ include')
changes[name]=text.replace(anchor,anchor+'\n#include "wr-iot-mcu-boot-irq-unmask.inc"')
for asset in ('mcu-boot-irq-unmask.inc','mcu-boot-irq-unmask-owner.inc'):
 changes['include/wr-iot-'+asset]=Path(__file__).with_name(asset).read_text()
for name,value in changes.items():(src/name).write_text(value)
hashes={n:hashlib.sha256((src/n).read_bytes()).hexdigest() for n in changes}
manifest['merged_driver_sha256'].update(hashes);manifest['candidate_driver_sha256'].update(hashes)
manifest['mcu_boot_irq_unmask']={'input_manifest_sha256':hashlib.sha256(raw).hexdigest(),'output_sha256':hashes,'scope':'MCU-only IRQ release with blocked rearm on failure; MAC/constructors closed, no epoch commit','target_compiled':False,'runtime_verified':False,'firmware_epoch_verified':False,'loader_bound':False}
mp.write_text(json.dumps(manifest,indent=2)+'\n')
