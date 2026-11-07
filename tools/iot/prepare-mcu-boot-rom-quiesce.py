#!/usr/bin/env python3
"""Prepare actual ROM/DMA/IRQ/MCU quiesce actor; ring rearm remains unfinished."""
import argparse
import hashlib
import json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('--install-isolated',action='store_true',required=True);a=p.parse_args()
src=a.source.resolve();mp=Path(str(src)+'.manifest.json');raw=mp.read_bytes();manifest=json.loads(raw)
actual={str(f.relative_to(src)):hashlib.sha256(f.read_bytes()).hexdigest() for f in src.rglob('*') if f.is_file()}
if (manifest.get('production_installed') is not False or manifest.get('target_compiled') is not False or
    'mcu_boot_freeze' not in manifest or 'mcu_boot_rom_quiesce' in manifest or actual!=manifest['merged_driver_sha256']):
 p.error('Expected unchanged isolated boot-freeze candidate')
mt=(src/'mcu/andes_mt.c').read_text();header=(src/'include/mcu/andes_mt.h').read_text()
anchor='#define SW_SYN0 0x81021250';assert mt.count(anchor)==1
mt=mt.replace(anchor,anchor+'\n#if defined(MT7603) && defined(MT_MAC) && defined(RTMP_PCI_SUPPORT)\n#include "wr-iot-mcu-dma-disabled-idle.inc"\n#include "wr-iot-mcu-boot-rom-quiesce.inc"\n#endif')
anchor='VOID AndesMTPciFwExit(struct _RTMP_ADAPTER *pAd);';assert header.count(anchor)==1
header=header.replace(anchor,anchor+'\n#if defined(MT7603) && defined(MT_MAC) && defined(RTMP_PCI_SUPPORT)\nINT32 wr_iot_mcu_boot_rom_quiesce(struct _RTMP_ADAPTER *ad);\n#endif')
changes={'mcu/andes_mt.c':mt,'include/mcu/andes_mt.h':header,'include/wr-iot-mcu-boot-rom-quiesce.inc':Path(__file__).with_name('mcu-boot-rom-quiesce.inc').read_text()}
for name,value in changes.items():(src/name).write_text(value)
hashes={n:hashlib.sha256((src/n).read_bytes()).hexdigest() for n in changes}
manifest['merged_driver_sha256'].update(hashes);manifest['candidate_driver_sha256'].update(hashes)
manifest['mcu_boot_rom_quiesce']={'input_manifest_sha256':hashlib.sha256(raw).hexdigest(),'output_sha256':hashes,'scope':'ROM-confirmed DMA/IRQ/RX/controller join actor; caller and ring rearm unfinished','target_compiled':False,'runtime_verified':False,'firmware_epoch_verified':False,'loader_bound':False}
mp.write_text(json.dumps(manifest,indent=2)+'\n')
