#!/usr/bin/env python3
"""Record Method1 checked restart/ROM observation bound to boot provenance."""
import argparse
import hashlib
import json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('--install-isolated',action='store_true',required=True);a=p.parse_args()
src=a.source.resolve();mp=Path(str(src)+'.manifest.json');raw=mp.read_bytes();manifest=json.loads(raw)
actual={str(f.relative_to(src)):hashlib.sha256(f.read_bytes()).hexdigest() for f in src.rglob('*') if f.is_file()}
if (manifest.get('production_installed') is not False or manifest.get('target_compiled') is not False or
    'mcu_boot_hardware' not in manifest or 'mcu_boot_rom_observe' in manifest or actual!=manifest['merged_driver_sha256']):
 p.error('Expected unchanged isolated boot hardware candidate')
names=('include/rtmp.h','include/mcu/andes_core.h','common/rtmp_init.c','mcu/andes_core.c')
changes={n:(src/n).read_text() for n in names}
def one(name,old,new):
 if changes[name].count(old)!=1:raise ValueError('Changed ring transaction anchor: '+name+': '+old)
 changes[name]=changes[name].replace(old,new)
one('include/rtmp.h','unsigned int wr_iot_boot_hw_state,wr_iot_boot_hw_stage;',
    'unsigned int wr_iot_boot_hw_state,wr_iot_boot_hw_stage,wr_iot_boot_rom_kind;\n unsigned long wr_iot_boot_rom_peer_serial,wr_iot_boot_rom_radio_serial,wr_iot_boot_rom_radio_epoch;')
one('common/rtmp_init.c','pAd->wr_iot_boot_hw_state=pAd->wr_iot_boot_hw_stage=0;',
    'pAd->wr_iot_boot_hw_state=pAd->wr_iot_boot_hw_stage=pAd->wr_iot_boot_rom_kind=0;\n        pAd->wr_iot_boot_rom_peer_serial=pAd->wr_iot_boot_rom_radio_serial=pAd->wr_iot_boot_rom_radio_epoch=0;')
one('include/mcu/andes_core.h','INT32 wr_iot_mcu_boot_hardware_prepare(struct _RTMP_ADAPTER *ad,const struct wr_iot_mcu_boot_ticket *ticket);',
    'INT32 wr_iot_mcu_boot_hardware_prepare(struct _RTMP_ADAPTER *ad,const struct wr_iot_mcu_boot_ticket *ticket);\nINT32 wr_iot_mcu_boot_rom_observe(struct _RTMP_ADAPTER *ad,const struct wr_iot_mcu_boot_ticket *ticket,unsigned int restart_acked);')
one('mcu/andes_core.c','#include "wr-iot-mcu-boot-hardware.inc"',
    '#include "wr-iot-mcu-boot-hardware.inc"\n#include "wr-iot-mcu-boot-rom-observe.inc"')
name='mcu/andes_mt.c';text=(src/name).read_text()
if text.count('#define TOP_MISC2 0x1134\n')!=1:raise ValueError('Unreviewed ROM register')
start=text.index('static NDIS_STATUS AndesMTLoadFwMethod1(');end=text.index('static NDIS_STATUS AndesMTLoadFwMethod2(',start);method=text[start:end]
def edit(old,new):
 global method
 if method.count(old)!=1:raise ValueError('Changed Method1 ROM receipt anchor: '+old)
 method=method.replace(old,new)
edit('\tstruct MCU_CTRL *Ctl = &ad->MCUCtrl;', '\tstruct MCU_CTRL *Ctl = &ad->MCUCtrl;\n#if defined(MT_MAC) && defined(RTMP_PCI_SUPPORT)\n unsigned int wr_iot_boot_restart_acked=0;\n#endif')
edit('\t\tret = CmdRestartDLReq(ad, boot);\n\n\t\tif (ret)\n\t\t\tgoto done;',
     '\t\tret = CmdRestartDLReq(ad, boot);\n\n\t\tif (ret)\n\t\t\tgoto done;\n#if defined(MT_MAC) && defined(RTMP_PCI_SUPPORT)\n        wr_iot_boot_restart_acked=1;\n#endif')
edit('\t/* standard CMD procedure */',
     '#if defined(MT_MAC) && defined(RTMP_PCI_SUPPORT)\n if(boot){\n  ret=wr_iot_mcu_boot_rom_observe(ad,boot,wr_iot_boot_restart_acked);\n  if(ret)goto done;\n }\n#endif\n\t/* standard CMD procedure */')
changes[name]=text[:start]+method+text[end:]
changes['include/wr-iot-mcu-boot-rom-observe.inc']=Path(__file__).with_name('mcu-boot-rom-observe.inc').read_text()
for name,value in changes.items():(src/name).write_text(value)
hashes={n:hashlib.sha256((src/n).read_bytes()).hexdigest() for n in changes}
manifest['merged_driver_sha256'].update(hashes);manifest['candidate_driver_sha256'].update(hashes)
manifest['mcu_boot_rom_observe']={'input_manifest_sha256':hashlib.sha256(raw).hexdigest(),'output_sha256':hashes,'scope':'Method1 ROM provenance after checked restart/ready loop; no epoch grant or ledger reset','target_compiled':False,'runtime_verified':False,'firmware_epoch_verified':False,'loader_bound':False}
mp.write_text(json.dumps(manifest,indent=2)+'\n')
