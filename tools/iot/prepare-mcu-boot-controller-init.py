#!/usr/bin/env python3
"""Prepare checked software controller initialization after ring transaction; no IRQ/DMA rearm."""
import argparse
import hashlib
import json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('--install-isolated',action='store_true',required=True);a=p.parse_args()
src=a.source.resolve();mp=Path(str(src)+'.manifest.json');raw=mp.read_bytes();manifest=json.loads(raw)
actual={str(f.relative_to(src)):hashlib.sha256(f.read_bytes()).hexdigest() for f in src.rglob('*') if f.is_file()}
if (manifest.get('production_installed') is not False or manifest.get('target_compiled') is not False or
    'mcu_checked_sequence_retirement' not in manifest or 'mcu_boot_controller_init' in manifest or actual!=manifest['merged_driver_sha256']):
 p.error('Expected unchanged isolated checked sequence retirement candidate')
names=('include/rtmp.h','include/mcu/andes_core.h','common/rtmp_init.c','mcu/andes_core.c')
changes={n:(src/n).read_text() for n in names}
def one(name,old,new):
 if changes[name].count(old)!=1:raise ValueError('Changed ring transaction anchor: '+name+': '+old)
 changes[name]=changes[name].replace(old,new)
one('include/rtmp.h','unsigned int wr_iot_boot_ring_stage,wr_iot_boot_ring_busy,wr_iot_boot_ring_failed;',
    'unsigned int wr_iot_boot_ring_stage,wr_iot_boot_ring_busy,wr_iot_boot_ring_failed,wr_iot_boot_ctrl_state;')
one('common/rtmp_init.c','pAd->wr_iot_boot_ring_stage=pAd->wr_iot_boot_ring_busy=pAd->wr_iot_boot_ring_failed=0;',
    'pAd->wr_iot_boot_ring_stage=pAd->wr_iot_boot_ring_busy=pAd->wr_iot_boot_ring_failed=pAd->wr_iot_boot_ctrl_state=0;')
core=changes['mcu/andes_core.c'];start=core.index('static VOID AndesCtrlPciInit(');end=core.index('\n}',start)+2
original=core[start:end]
if hashlib.sha256(original.encode()).hexdigest()!='ae90a56b11de21d3076252fe7d6d233797280f7c352ca32ccbf31515fa2510a3':raise ValueError('Unreviewed PCI controller initializer')
checked=original.replace('static VOID AndesCtrlPciInit(', 'static INT32 wr_iot_boot_ctrl_pci_init(')
line='\tRTMP_OS_TASKLET_INIT(ad, &ctl->cmd_msg_task, AndesCmdMsgBh, (unsigned long)ad);'
if checked.count(line)!=1:raise ValueError('Unreviewed controller tasklet initializer')
checked=checked.replace(line,'#ifdef OS_ABL_FUNC_SUPPORT\n\tif(!RTMP_OS_TASKLET_INIT(ad, &ctl->cmd_msg_task, AndesCmdMsgBh, (unsigned long)ad))return NDIS_STATUS_FAILURE;\n#else\n'+line+'\n#endif')
checked=checked[:-2]+'\n ctl->power_on=FALSE;ctl->dpd_on=FALSE;ctl->RxStream0=0;ctl->RxStream1=0;\n return NDIS_STATUS_SUCCESS;\n}'
one('mcu/andes_core.c','#include "wr-iot-mcu-boot-ring-transaction.inc"',
    '#include "wr-iot-mcu-boot-ring-transaction.inc"\n#include "wr-iot-mcu-boot-controller-init.inc"')
one('include/mcu/andes_core.h','INT32 wr_iot_mcu_boot_ring_transaction(struct _RTMP_ADAPTER *ad,const struct wr_iot_mcu_boot_ticket *ticket);',
    'INT32 wr_iot_mcu_boot_ring_transaction(struct _RTMP_ADAPTER *ad,const struct wr_iot_mcu_boot_ticket *ticket);\nINT32 wr_iot_mcu_boot_controller_init(struct _RTMP_ADAPTER *ad);')
changes['include/wr-iot-mcu-boot-controller-init.inc']=checked+'\n'+Path(__file__).with_name('mcu-boot-controller-init.inc').read_text()
for name,value in changes.items():(src/name).write_text(value)
hashes={n:hashlib.sha256((src/n).read_bytes()).hexdigest() for n in changes}
manifest['merged_driver_sha256'].update(hashes);manifest['candidate_driver_sha256'].update(hashes)
manifest['mcu_boot_controller_init']={'input_manifest_sha256':hashlib.sha256(raw).hexdigest(),'output_sha256':hashes,'scope':'checked software controller init only; no ledger reset, IRQ/DMA enable or loader binding','target_compiled':False,'runtime_verified':False,'firmware_epoch_verified':False,'loader_bound':False}
mp.write_text(json.dumps(manifest,indent=2)+'\n')
