#!/usr/bin/env python3
"""Replenish successful checked IDs only at the complete frozen ROM/RX boundary."""
import argparse
import hashlib
import json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('--install-isolated',action='store_true',required=True);a=p.parse_args()
src=a.source.resolve();mp=Path(str(src)+'.manifest.json');raw=mp.read_bytes();manifest=json.loads(raw)
actual={str(f.relative_to(src)):hashlib.sha256(f.read_bytes()).hexdigest() for f in src.rglob('*') if f.is_file()}
if (manifest.get('production_installed') is not False or manifest.get('target_compiled') is not False or
    'mcu_boot_rom_observe' not in manifest or 'mcu_boot_retired_boundary' in manifest or actual!=manifest['merged_driver_sha256']):
 p.error('Expected unchanged isolated ROM provenance candidate')
names=('include/rtmp.h','include/mcu/andes_core.h','common/rtmp_init.c','mcu/andes_core.c')
changes={n:(src/n).read_text() for n in names}
def one(name,old,new):
 if changes[name].count(old)!=1:raise ValueError('Changed ring transaction anchor: '+name+': '+old)
 changes[name]=changes[name].replace(old,new)
one('include/rtmp.h','unsigned int wr_iot_boot_hw_state,wr_iot_boot_hw_stage,wr_iot_boot_rom_kind;',
    'unsigned int wr_iot_boot_hw_state,wr_iot_boot_hw_stage,wr_iot_boot_rom_kind;\n unsigned int wr_iot_boot_epoch_done,wr_iot_boot_epoch_retired_mask;\n unsigned long wr_iot_boot_epoch_radio_serial,wr_iot_boot_epoch_radio_epoch;')
one('common/rtmp_init.c','pAd->wr_iot_boot_hw_state=pAd->wr_iot_boot_hw_stage=pAd->wr_iot_boot_rom_kind=0;',
    'pAd->wr_iot_boot_hw_state=pAd->wr_iot_boot_hw_stage=pAd->wr_iot_boot_rom_kind=0;\n        pAd->wr_iot_boot_epoch_done=pAd->wr_iot_boot_epoch_retired_mask=0;\n        pAd->wr_iot_boot_epoch_radio_serial=pAd->wr_iot_boot_epoch_radio_epoch=0;')
one('include/mcu/andes_core.h','INT32 wr_iot_mcu_boot_rom_observe(struct _RTMP_ADAPTER *ad,const struct wr_iot_mcu_boot_ticket *ticket,unsigned int restart_acked);',
    'INT32 wr_iot_mcu_boot_rom_observe(struct _RTMP_ADAPTER *ad,const struct wr_iot_mcu_boot_ticket *ticket,unsigned int restart_acked);\nINT32 wr_iot_mcu_boot_retired_boundary(struct _RTMP_ADAPTER *ad,const struct wr_iot_mcu_boot_ticket *ticket);')
one('mcu/andes_core.c','#include "wr-iot-mcu-boot-rom-observe.inc"',
    '#include "wr-iot-mcu-boot-rom-observe.inc"\n#include "wr-iot-mcu-boot-retired-boundary.inc"')
name='include/wr-iot-mcu-boot-hardware.inc';text=(src/name).read_text()
anchor=' if(wr_iot_mcu_boot_controller_init(ad)!=NDIS_STATUS_SUCCESS||'
if text.count(anchor)!=1:raise ValueError('Unreviewed hardware stage boundary')
changes[name]=text.replace(anchor,' if(wr_iot_mcu_boot_retired_boundary(ad,ticket)!=NDIS_STATUS_SUCCESS)goto done;\n'+anchor)
changes['include/wr-iot-mcu-boot-retired-boundary.inc']=Path(__file__).with_name('mcu-boot-retired-boundary.inc').read_text()
for name,value in changes.items():(src/name).write_text(value)
hashes={n:hashlib.sha256((src/n).read_bytes()).hexdigest() for n in changes}
manifest['merged_driver_sha256'].update(hashes);manifest['candidate_driver_sha256'].update(hashes)
manifest['mcu_boot_retired_boundary']={'input_manifest_sha256':hashlib.sha256(raw).hexdigest(),'output_sha256':hashes,'scope':'retired-ID replenishment after frozen ROM/PSE/RX/ring transaction; poison/quarantine untouched, no admission or runtime grant','target_compiled':False,'runtime_verified':False,'firmware_epoch_verified':False,'loader_bound':False}
mp.write_text(json.dumps(manifest,indent=2)+'\n')
