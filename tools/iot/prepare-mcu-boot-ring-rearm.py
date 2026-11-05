#!/usr/bin/env python3
"""Prepare narrow CTRL/RX register programming with DMA disabled; epoch commit remains unfinished."""
import argparse
import hashlib
import json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('--install-isolated',action='store_true',required=True);a=p.parse_args()
src=a.source.resolve();mp=Path(str(src)+'.manifest.json');raw=mp.read_bytes();manifest=json.loads(raw)
actual={str(f.relative_to(src)):hashlib.sha256(f.read_bytes()).hexdigest() for f in src.rglob('*') if f.is_file()}
if (manifest.get('production_installed') is not False or manifest.get('target_compiled') is not False or
    'mcu_boot_control_retire' not in manifest or 'mcu_boot_ring_rearm' in manifest or actual!=manifest['merged_driver_sha256']):
 p.error('Expected unchanged isolated control retirement candidate')
sdk=(src/'include/mac/mac_mt/mt_mac_pci.h').read_text()
start=sdk.rfind('#ifdef RT_BIG_ENDIAN',0,sdk.index('typedef\tstruct GNU_PACKED _TXD_STRUC'))
end=sdk.index('#endif /* RT_BIG_ENDIAN */',start)+len('#endif /* RT_BIG_ENDIAN */')
if hashlib.sha256(sdk[start:end].encode()).hexdigest()!='1cd95981c728ab7d7fd34b8a81c89186df58ed8a3ecf92242081f201e120eb75':raise ValueError('Unreviewed MT TX descriptor layout')
reviewed=(src/'mac/mt_mac.c').read_text();start=reviewed.index('VOID mt_asic_init_txrx_ring(');end=reviewed.index('\n}',start)+2
if hashlib.sha256(reviewed[start:end].encode()).hexdigest()!='d3430dd77f903a0e75fc8231cc323dc5c18e76d84affeac0b525627bc1c9b07a':raise ValueError('Unreviewed MT ring initialization')
source=(src/'common/cmm_data_pci.c').read_text();header=(src/'include/rtmp.h').read_text()
source+='\n#if defined(MT7603) && defined(MT_MAC) && defined(RTMP_PCI_SUPPORT)\n#include "wr-iot-mcu-boot-ring-rearm.inc"\n#endif\n'
anchor='INT RtmpNetTaskExit(RTMP_ADAPTER *pAd);';assert header.count(anchor)==1
header=header.replace(anchor,anchor+'\n#if defined(MT7603) && defined(MT_MAC) && defined(RTMP_PCI_SUPPORT)\nINT wr_iot_mcu_boot_ring_rearm(RTMP_ADAPTER *ad);\n#endif')
changes={'common/cmm_data_pci.c':source,'include/rtmp.h':header,'include/wr-iot-mcu-boot-ring-rearm.inc':Path(__file__).with_name('mcu-boot-ring-rearm.inc').read_text()}
for name,value in changes.items():(src/name).write_text(value)
hashes={n:hashlib.sha256((src/n).read_bytes()).hexdigest() for n in changes}
manifest['merged_driver_sha256'].update(hashes);manifest['candidate_driver_sha256'].update(hashes)
manifest['mcu_boot_ring_rearm']={'input_manifest_sha256':hashlib.sha256(raw).hexdigest(),'output_sha256':hashes,'reviewed_descriptor_header_sha256':actual['include/mac/mac_mt/mt_mac_pci.h'],'scope':'narrow CTRL5/RX0/RX1 reset and register readback with DMA disabled; no firmware epoch commit or loader binding','target_compiled':False,'runtime_verified':False,'firmware_epoch_verified':False,'loader_bound':False}
mp.write_text(json.dumps(manifest,indent=2)+'\n')
