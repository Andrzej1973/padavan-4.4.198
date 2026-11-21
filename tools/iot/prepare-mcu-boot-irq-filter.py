#!/usr/bin/env python3
"""Restrict raw bootstrap ISR sources before any WF/data handler runs."""
import argparse
import hashlib
import json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('source',type=Path)
p.add_argument('--install-isolated',action='store_true',required=True)
a=p.parse_args();src=a.source.resolve();mp=Path(str(src)+'.manifest.json')
raw=mp.read_bytes();manifest=json.loads(raw)
actual={str(f.relative_to(src)):hashlib.sha256(f.read_bytes()).hexdigest() for f in src.rglob('*') if f.is_file()}
if (manifest.get('production_installed') is not False or manifest.get('target_compiled') is not False or
    'mcu_boot_dma_start' not in manifest or 'mcu_boot_irq_filter' in manifest or
    actual!=manifest['merged_driver_sha256']):
 p.error('Expected unchanged isolated checked DMA candidate')
name='os/linux/rt_rbus_pci_drv.c';text=(src/name).read_text()
anchor='\t\tRTMP_IO_READ32(pAd, MT_INT_SOURCE_CSR, &IntSource);'
if text.count(anchor)!=1:raise ValueError('Unreviewed ISR source read')
text=text.replace(anchor,anchor+'''
        /* A raw pending bit can be set even while its IRQ is masked. */
        if (pAd->wr_iot_boot_active) {
            if (IntSource == ~(UINT32)0) {
                RTMP_SET_FLAG(pAd, fRTMP_ADAPTER_NIC_NOT_EXIST | fRTMP_ADAPTER_HALT_IN_PROGRESS);
                return;
            }
            IntSource &= MT_INT_RX_CMD | MT_INT_CMD;
        }
''')
(src/name).write_text(text);hashes={name:hashlib.sha256((src/name).read_bytes()).hexdigest()}
manifest['merged_driver_sha256'].update(hashes);manifest['candidate_driver_sha256'].update(hashes)
manifest['mcu_boot_irq_filter']={
 'input_manifest_sha256':hashlib.sha256(raw).hexdigest(),'output_sha256':hashes,
 'scope':'filter raw bootstrap ISR sources before WF/data handlers; preserve ordinary path and NIC removal',
 'target_compiled':False,'runtime_verified':False,'firmware_epoch_verified':False}
mp.write_text(json.dumps(manifest,indent=2)+'\n')
