#!/usr/bin/env python3
"""Prepare explicit MCU-only tasklet restart while command construction stays frozen."""
import argparse
import hashlib
import json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('--install-isolated',action='store_true',required=True);a=p.parse_args()
src=a.source.resolve();mp=Path(str(src)+'.manifest.json');raw=mp.read_bytes();manifest=json.loads(raw)
actual={str(f.relative_to(src)):hashlib.sha256(f.read_bytes()).hexdigest() for f in src.rglob('*') if f.is_file()}
if (manifest.get('production_installed') is not False or manifest.get('target_compiled') is not False or
    'mcu_boot_controller_init' not in manifest or 'mcu_boot_rx_restart' in manifest or actual!=manifest['merged_driver_sha256']):
 p.error('Expected unchanged isolated controller initialization candidate')
names=('include/rtmp.h','include/mcu/andes_core.h','common/rtmp_init.c','mcu/andes_core.c')
changes={n:(src/n).read_text() for n in names}
def one(name,old,new):
 if changes[name].count(old)!=1:raise ValueError('Changed ring transaction anchor: '+name+': '+old)
 changes[name]=changes[name].replace(old,new)
one('include/rtmp.h','wr_iot_boot_ring_failed,wr_iot_boot_ctrl_state;',
    'wr_iot_boot_ring_failed,wr_iot_boot_ctrl_state,wr_iot_boot_rx_state;')
one('common/rtmp_init.c','pAd->wr_iot_boot_ring_failed=pAd->wr_iot_boot_ctrl_state=0;',
    'pAd->wr_iot_boot_ring_failed=pAd->wr_iot_boot_ctrl_state=pAd->wr_iot_boot_rx_state=0;')
one('include/rtmp.h','INT RtmpNetTaskExit(RTMP_ADAPTER *pAd);',
    'INT RtmpNetTaskExit(RTMP_ADAPTER *pAd);\nINT wr_iot_nettask_boot_rx_restart(RTMP_ADAPTER *pAd);')
one('include/mcu/andes_core.h','INT32 wr_iot_mcu_boot_controller_init(struct _RTMP_ADAPTER *ad);',
    'INT32 wr_iot_mcu_boot_controller_init(struct _RTMP_ADAPTER *ad);\nINT32 wr_iot_mcu_boot_rx_restart_owned(struct _RTMP_ADAPTER *ad);\nINT32 wr_iot_mcu_boot_rx_restart(struct _RTMP_ADAPTER *ad);')
one('mcu/andes_core.c','#include "wr-iot-mcu-boot-controller-init.inc"',
    '#include "wr-iot-mcu-boot-controller-init.inc"\n#include "wr-iot-mcu-dma-disabled-idle.inc"\n#include "wr-iot-mcu-boot-rx-restart.inc"')
if (src/'mcu/andes_mt.c').read_text().count('#define TOP_MISC2 0x1134\n')!=1:raise ValueError('Unreviewed ROM register')
name='include/wr-iot-mcu-nettask-bootstrap.inc'
net=(src/name).read_text()
old='static INT wr_iot_boot_nettask_init(RTMP_ADAPTER *pAd)'
if net.count(old)!=1 or net.count('wr_iot_mcu_boot_owned(pAd)')!=2:raise ValueError('Unreviewed MCU nettask initializer')
net=net.replace(old,'static INT wr_iot_boot_nettask_init(RTMP_ADAPTER *pAd,unsigned int restart)')
net=net.replace('wr_iot_mcu_boot_owned(pAd)','(restart?wr_iot_mcu_boot_rx_restart_owned(pAd):wr_iot_mcu_boot_owned(pAd))')
net+='\nINT wr_iot_nettask_boot_rx_restart(RTMP_ADAPTER *pAd)\n{\n if(!pAd)return NDIS_STATUS_FAILURE;\n return wr_iot_boot_nettask_init(pAd,1);\n}\n'
changes[name]=net
name='os/linux/rt_rbus_pci_drv.c';net=(src/name).read_text();old='wr_iot_boot_nettask_init(pAd);'
if net.count(old)!=1:raise ValueError('Unreviewed MCU nettask entry')
changes[name]=net.replace(old,'wr_iot_boot_nettask_init(pAd,0);')
changes['include/wr-iot-mcu-boot-rx-restart.inc']=Path(__file__).with_name('mcu-boot-rx-restart.inc').read_text()
for name,value in changes.items():(src/name).write_text(value)
hashes={n:hashlib.sha256((src/n).read_bytes()).hexdigest() for n in changes}
manifest['merged_driver_sha256'].update(hashes);manifest['candidate_driver_sha256'].update(hashes)
manifest['mcu_boot_rx_restart']={'input_manifest_sha256':hashlib.sha256(raw).hexdigest(),'output_sha256':hashes,'scope':'explicit frozen-owner MCU tasklet recreation; no IRQ/DMA enable, ledger reset or loader binding','target_compiled':False,'runtime_verified':False,'firmware_epoch_verified':False,'loader_bound':False}
mp.write_text(json.dumps(manifest,indent=2)+'\n')
