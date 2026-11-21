#!/usr/bin/env python3
"""Prepare bounded known-queue snapshot; no queue removal or epoch commit."""
import argparse
import hashlib
import json
import re
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('--install-isolated',action='store_true',required=True);a=p.parse_args()
src=a.source.resolve();mp=Path(str(src)+'.manifest.json');raw=mp.read_bytes();manifest=json.loads(raw)
actual={str(f.relative_to(src)):hashlib.sha256(f.read_bytes()).hexdigest() for f in src.rglob('*') if f.is_file()}
if (manifest.get('production_installed') is not False or manifest.get('target_compiled') is not False or
    'mcu_boot_rom_quiesce' not in manifest or 'mcu_boot_pse_empty' in manifest or actual!=manifest['merged_driver_sha256']):
 p.error('Expected unchanged isolated ROM-quiesce candidate')
info=(src/'common/cmm_info.c').read_text()
known={(int(x),int(y)) for x,y in re.findall(r'DumpPseFrameInfo\(pAd,\s*(\d+),\s*(\d+)\)',info)}
expected={(port,q) for port,limit in enumerate((3,4,14)) for q in range(limit)}
if known!=expected:raise ValueError('Changed SDK diagnostic PSE queue inventory')
mt=(src/'mcu/andes_mt.c').read_text();header=(src/'include/mcu/andes_mt.h').read_text()
anchor='#include "wr-iot-mcu-boot-rom-quiesce.inc"';assert mt.count(anchor)==1
mt=mt.replace(anchor,anchor+'\n#include "wr-iot-mcu-boot-pse-empty.inc"')
anchor='INT32 wr_iot_mcu_boot_rom_quiesce(struct _RTMP_ADAPTER *ad);';assert header.count(anchor)==1
header=header.replace(anchor,anchor+'\nBOOLEAN wr_iot_mcu_boot_pse_empty(struct _RTMP_ADAPTER *ad);')
data=(src/'common/cmm_data.c').read_text()
for old,new in (('ad->wr_iot_boot_mcu_only && rx_pkt_type','ad->wr_iot_boot_active && rx_pkt_type'),('!ad->wr_iot_boot_mcu_only && ad->chipOps.rx_event_handler','!ad->wr_iot_boot_active && ad->chipOps.rx_event_handler')):
 if data.count(old)!=1:raise ValueError('Changed bootstrap RX restriction')
 data=data.replace(old,new)
changes={'mcu/andes_mt.c':mt,'include/mcu/andes_mt.h':header,'common/cmm_data.c':data,'include/wr-iot-mcu-boot-pse-empty.inc':Path(__file__).with_name('mcu-boot-pse-empty.inc').read_text()}
for name,value in changes.items():(src/name).write_text(value)
hashes={n:hashlib.sha256((src/n).read_bytes()).hexdigest() for n in changes}
manifest['merged_driver_sha256'].update(hashes);manifest['candidate_driver_sha256'].update(hashes)
manifest['mcu_boot_pse_empty']={'input_manifest_sha256':hashlib.sha256(raw).hexdigest(),'output_sha256':hashes,'reviewed_source_sha256':{n:actual[n] for n in ('common/cmm_info.c','include/mac/mac_mt/pse.h')},'scope':'two bounded known-queue snapshots under ROM/MAC/DMA/IRQ/join preconditions; no queue removal or epoch proof','target_compiled':False,'runtime_verified':False,'firmware_epoch_verified':False,'loader_bound':False}
mp.write_text(json.dumps(manifest,indent=2)+'\n')
