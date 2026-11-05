#!/usr/bin/env python3
"""Compose live-RX PSE drain with ROM quiesce; ring rearm still unfinished."""
import argparse
import hashlib
import json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('--install-isolated',action='store_true',required=True);a=p.parse_args()
src=a.source.resolve();mp=Path(str(src)+'.manifest.json');raw=mp.read_bytes();manifest=json.loads(raw)
actual={str(f.relative_to(src)):hashlib.sha256(f.read_bytes()).hexdigest() for f in src.rglob('*') if f.is_file()}
if (manifest.get('production_installed') is not False or manifest.get('target_compiled') is not False or
    'mcu_boot_rx_discard' not in manifest or 'mcu_boot_pse_drain' in manifest or actual!=manifest['merged_driver_sha256']):
 p.error('Expected unchanged isolated RX-discard candidate')
names=('mcu/andes_mt.c','include/mcu/andes_mt.h','include/wr-iot-mcu-boot-rom-quiesce.inc')
changes={n:(src/n).read_text() for n in names}
def one(name,old,new):
 if changes[name].count(old)!=1:raise ValueError('Changed PSE drain anchor: '+name+': '+old)
 changes[name]=changes[name].replace(old,new)
one('mcu/andes_mt.c','#include "wr-iot-mcu-boot-pse-empty.inc"',
    '#include "wr-iot-mcu-boot-pse-empty.inc"\n#include "wr-iot-mcu-boot-pse-drain.inc"')
one('include/mcu/andes_mt.h','BOOLEAN wr_iot_mcu_boot_pse_empty(struct _RTMP_ADAPTER *ad);',
    'BOOLEAN wr_iot_mcu_boot_pse_empty(struct _RTMP_ADAPTER *ad);\nINT32 wr_iot_mcu_boot_pse_drain(struct _RTMP_ADAPTER *ad,unsigned int live_rx);')
name='include/wr-iot-mcu-boot-rom-quiesce.inc'
one(name,''' AndesMTPciFwExit(ad);
 RTMP_IO_READ32(ad,MT_INT_MASK_CSR,&value);
 if(value!=0 || !wr_iot_mcu_dma_disabled_idle(ad))return NDIS_STATUS_FAILURE;
 /* IRQ remains registered. No lock is held across synchronization/joins. */
 synchronize_irq(cookie->pci_dev->irq);
 if(RtmpNetTaskExit(ad)!=NDIS_STATUS_SUCCESS)return NDIS_STATUS_FAILURE;''',
''' if(!AsicSetMacTxRx(ad,ASIC_MAC_TXRX,FALSE))return NDIS_STATUS_FAILURE;
 RTMP_IO_READ32(ad,ARB_SCR,&value);
 if(value==~(UINT32)0||(value&(MT_ARB_SCR_TXDIS|MT_ARB_SCR_RXDIS))!=
    (MT_ARB_SCR_TXDIS|MT_ARB_SCR_RXDIS))return NDIS_STATUS_FAILURE;
 RTMP_ASIC_INTERRUPT_DISABLE(ad);
 RTMP_IO_READ32(ad,MT_INT_MASK_CSR,&value);
 if(value)return NDIS_STATUS_FAILURE;
 synchronize_irq(cookie->pci_dev->irq);
 if(RtmpNetTaskExit(ad)!=NDIS_STATUS_SUCCESS)return NDIS_STATUS_FAILURE;
 /* A last tasklet may have reenabled its IRQ before join completed. */
 RTMP_ASIC_INTERRUPT_DISABLE(ad);
 RTMP_IO_READ32(ad,MT_INT_MASK_CSR,&value);
 if(value)return NDIS_STATUS_FAILURE;
 synchronize_irq(cookie->pci_dev->irq);
 if(wr_iot_mcu_boot_pse_drain(ad,1)!=NDIS_STATUS_SUCCESS)return NDIS_STATUS_FAILURE;
 AndesMTPciFwExit(ad);
 RTMP_IO_READ32(ad,MT_INT_MASK_CSR,&value);
 if(value || !wr_iot_mcu_dma_disabled_idle(ad))return NDIS_STATUS_FAILURE;
 synchronize_irq(cookie->pci_dev->irq);
 if(wr_iot_mcu_boot_pse_drain(ad,0)!=NDIS_STATUS_SUCCESS)return NDIS_STATUS_FAILURE;''')
one(name,'if(value || !wr_iot_mcu_dma_disabled_idle(ad))return NDIS_STATUS_FAILURE;\n return NDIS_STATUS_SUCCESS;',
    'if(value || !wr_iot_mcu_dma_disabled_idle(ad) || !wr_iot_mcu_boot_pse_empty(ad))return NDIS_STATUS_FAILURE;\n return NDIS_STATUS_SUCCESS;')
changes['include/wr-iot-mcu-boot-pse-drain.inc']=Path(__file__).with_name('mcu-boot-pse-drain.inc').read_text()
for name,value in changes.items():(src/name).write_text(value)
hashes={n:hashlib.sha256((src/n).read_bytes()).hexdigest() for n in changes}
manifest['merged_driver_sha256'].update(hashes);manifest['candidate_driver_sha256'].update(hashes)
manifest['mcu_boot_pse_drain']={'input_manifest_sha256':hashlib.sha256(raw).hexdigest(),'output_sha256':hashes,'scope':'bounded live RX discard/PSE drain, then DMA stop and final discard/join; no ring rearm or epoch commit','target_compiled':False,'runtime_verified':False,'firmware_epoch_verified':False,'loader_bound':False}
mp.write_text(json.dumps(manifest,indent=2)+'\n')
