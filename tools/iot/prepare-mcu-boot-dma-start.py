#!/usr/bin/env python3
"""Prepare checked shared DMA start/stop, leaving IRQ and MAC masked."""
import argparse
import hashlib
import json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('--install-isolated',action='store_true',required=True);a=p.parse_args()
src=a.source.resolve();mp=Path(str(src)+'.manifest.json');raw=mp.read_bytes();manifest=json.loads(raw)
actual={str(f.relative_to(src)):hashlib.sha256(f.read_bytes()).hexdigest() for f in src.rglob('*') if f.is_file()}
if (manifest.get('production_installed') is not False or manifest.get('target_compiled') is not False or
    'mcu_boot_irq_prepare' not in manifest or 'mcu_boot_dma_start' in manifest or actual!=manifest['merged_driver_sha256']):
 p.error('Expected unchanged isolated IRQ preparation candidate')
names=('include/rtmp.h','include/mcu/andes_core.h','common/rtmp_init.c','mcu/andes_core.c')
changes={n:(src/n).read_text() for n in names}
def one(name,old,new):
 if changes[name].count(old)!=1:raise ValueError('Changed ring transaction anchor: '+name+': '+old)
 changes[name]=changes[name].replace(old,new)
one('include/rtmp.h','wr_iot_boot_rx_state,wr_iot_boot_irq_state;',
    'wr_iot_boot_rx_state,wr_iot_boot_irq_state;\n unsigned int wr_iot_boot_dma_state,wr_iot_boot_dma_saved_off,wr_iot_boot_dma_saved_valid,wr_iot_boot_dma_stop_verified;')
one('common/rtmp_init.c','pAd->wr_iot_boot_rx_state=pAd->wr_iot_boot_irq_state=0;',
    'pAd->wr_iot_boot_rx_state=pAd->wr_iot_boot_irq_state=0;\n        pAd->wr_iot_boot_dma_state=pAd->wr_iot_boot_dma_saved_off=pAd->wr_iot_boot_dma_saved_valid=pAd->wr_iot_boot_dma_stop_verified=0;')
one('include/mcu/andes_core.h','INT32 wr_iot_mcu_boot_irq_prepare(struct _RTMP_ADAPTER *ad);',
    'INT32 wr_iot_mcu_boot_irq_prepare(struct _RTMP_ADAPTER *ad);\nINT32 wr_iot_mcu_boot_dma_owned(struct _RTMP_ADAPTER *ad);\nINT32 wr_iot_mcu_boot_dma_start(struct _RTMP_ADAPTER *ad);')
one('mcu/andes_core.c','#include "wr-iot-mcu-boot-irq-owner.inc"',
    '#include "wr-iot-mcu-boot-irq-owner.inc"\n#include "wr-iot-mcu-boot-dma-owner.inc"')
name='include/mcu/andes_mt.h';text=(src/name).read_text();anchor='INT32 wr_iot_mcu_boot_rom_quiesce(struct _RTMP_ADAPTER *ad);'
if text.count(anchor)!=1:raise ValueError('Unreviewed ROM actor prototype')
changes[name]=text.replace(anchor,anchor+'\nINT32 wr_iot_mcu_boot_dma_start_hw(struct _RTMP_ADAPTER *ad);\nINT32 wr_iot_mcu_boot_dma_stop_hw(struct _RTMP_ADAPTER *ad);')
name='mcu/andes_mt.c';text=(src/name).read_text();anchor='#include "wr-iot-mcu-boot-pse-drain.inc"'
if text.count(anchor)!=1:raise ValueError('Unreviewed MCU include order')
changes[name]=text.replace(anchor,anchor+'\n#include "wr-iot-mcu-boot-dma-start.inc"')
for asset in ('mcu-boot-dma-start.inc','mcu-boot-dma-owner.inc'):
 changes['include/wr-iot-'+asset]=Path(__file__).with_name(asset).read_text()
for name,value in changes.items():(src/name).write_text(value)
hashes={n:hashlib.sha256((src/n).read_bytes()).hexdigest() for n in changes}
manifest['merged_driver_sha256'].update(hashes);manifest['candidate_driver_sha256'].update(hashes)
manifest['mcu_boot_dma_start']={'input_manifest_sha256':hashlib.sha256(raw).hexdigest(),'output_sha256':hashes,'scope':'checked DMA-only enable with readback and retained failure stop; IRQ/MAC/constructors closed, no epoch commit','target_compiled':False,'runtime_verified':False,'firmware_epoch_verified':False,'loader_bound':False}
mp.write_text(json.dumps(manifest,indent=2)+'\n')
