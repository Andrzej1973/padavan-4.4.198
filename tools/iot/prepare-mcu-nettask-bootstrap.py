#!/usr/bin/env python3
"""Bind actual nettask init/exit to an owned MCU-only bootstrap lane."""
import argparse
import hashlib
import json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('--install-isolated',action='store_true',required=True);a=p.parse_args()
src=a.source.resolve();mp=Path(str(src)+'.manifest.json');raw=mp.read_bytes();manifest=json.loads(raw)
actual={str(f.relative_to(src)):hashlib.sha256(f.read_bytes()).hexdigest() for f in src.rglob('*') if f.is_file()}
if (manifest.get('production_installed') is not False or manifest.get('target_compiled') is not False or
    'mcu_boot_loader' not in manifest or 'mcu_nettask_bootstrap' in manifest or actual!=manifest['merged_driver_sha256']):
 p.error('Expected unchanged isolated boot-loader candidate')
names=('include/rtmp.h','include/mcu/andes_core.h','common/rtmp_init.c','include/wr-iot-mcu-boot-transport.inc','os/linux/rt_rbus_pci_drv.c','common/cmm_data.c')
changes={n:(src/n).read_text() for n in names}
def one(name,old,new):
 if changes[name].count(old)!=1:raise ValueError('Changed MCU nettask anchor: '+name+': '+old)
 changes[name]=changes[name].replace(old,new)
one('include/rtmp.h','unsigned int wr_iot_boot_active,wr_iot_boot_failed;',
    'unsigned int wr_iot_boot_active,wr_iot_boot_failed,wr_iot_boot_mcu_only;')
one('common/rtmp_init.c','pAd->wr_iot_boot_active=pAd->wr_iot_boot_failed=0;',
    'pAd->wr_iot_boot_active=pAd->wr_iot_boot_failed=pAd->wr_iot_boot_mcu_only=0;')
one('include/mcu/andes_core.h','INT32 wr_iot_mcu_boot_reserve(',
    'INT32 wr_iot_mcu_boot_owned(struct _RTMP_ADAPTER *ad);\nINT32 wr_iot_mcu_boot_reserve(')
changes['include/wr-iot-mcu-boot-transport.inc']+='''
/* Snapshot revalidation; caller also reserves the nettask initialization gate.
 * The physical open owner serializes boot init/exit and pins adapter lifetime. */
INT32 wr_iot_mcu_boot_owned(RTMP_ADAPTER *ad)
{
 ULONG flags=0,owner_flags=0;int ready;
 if(!ad||!wr_iot_mcu_boot_peer_matches(ad,ad->wr_iot_boot_ticket.peer_serial))return 0;
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 RTMP_SPIN_LOCK_IRQSAVE(&ad->wr_iot_mcu_sender_lock,&owner_flags);
 ready=wr_iot_mcu_boot_matches(ad,&ad->wr_iot_boot_ticket);
 RTMP_SPIN_UNLOCK_IRQRESTORE(&ad->wr_iot_mcu_sender_lock,&owner_flags);
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 return ready;
}
'''
net='os/linux/rt_rbus_pci_drv.c'
one(net,'#include "wr-iot-nettask-schedule.inc"',
    '#include "wr-iot-nettask-schedule.inc"\n#if defined(MT_MAC) && defined(RTMP_PCI_SUPPORT) && defined(CONFIG_ANDES_SUPPORT)\n#include "wr-iot-mcu-nettask-bootstrap.inc"\n#endif')
one(net,' unsigned int wr_count=0;ULONG wr_flags = 0;',
    ' unsigned int wr_count=0;ULONG wr_flags = 0;\n'
    '#if defined(MT_MAC) && defined(RTMP_PCI_SUPPORT) && defined(CONFIG_ANDES_SUPPORT)\n'
    ' if(pAd->wr_iot_boot_active)return wr_iot_boot_nettask_init(pAd);\n#endif')
start=changes[net].index('INT RtmpNetTaskExit(');end=changes[net].index('\n}',start)+2
body=changes[net][start:end];anchor=' ULONG wr_flags = 0;int wr_joined;'
if body.count(anchor)!=1:raise ValueError('Changed global nettask exit declaration')
body=body.replace(anchor,anchor+'\n#if defined(MT_MAC) && defined(RTMP_PCI_SUPPORT) && defined(CONFIG_ANDES_SUPPORT)\n if(pAd->wr_iot_boot_mcu_only)return wr_iot_boot_nettask_exit(pAd);\n#endif')
changes[net]=changes[net][:start]+body+changes[net][end:]
one('common/cmm_data.c','rx_pkt_type = RMAC_RX_PKT_TYPE(rxd_0->word);',
    'rx_pkt_type = RMAC_RX_PKT_TYPE(rxd_0->word);\n'
    '#if defined(MT_MAC) && defined(RTMP_PCI_SUPPORT) && defined(CONFIG_ANDES_SUPPORT)\n'
    '    if (ad->wr_iot_boot_mcu_only && rx_pkt_type!=RMAC_RX_PKT_TYPE_RX_EVENT) return 0;\n'
    '#endif')
one('common/cmm_data.c','if (ad->chipOps.rx_event_handler != NULL)',
    'if (!ad->wr_iot_boot_mcu_only && ad->chipOps.rx_event_handler != NULL)')
changes['include/wr-iot-mcu-nettask-bootstrap.inc']=Path(__file__).with_name('mcu-nettask-bootstrap.inc').read_text()
for name,value in changes.items():(src/name).write_text(value)
hashes={n:hashlib.sha256((src/n).read_bytes()).hexdigest() for n in changes}
manifest['merged_driver_sha256'].update(hashes);manifest['candidate_driver_sha256'].update(hashes)
manifest['mcu_nettask_bootstrap']={'input_manifest_sha256':hashlib.sha256(raw).hexdigest(),'output_sha256':hashes,'scope':'owned MCU-only nettask init/exit; reservation/open and epoch commit unfinished','target_compiled':False,'runtime_verified':False,'ordinary_data_rearmed':False}
mp.write_text(json.dumps(manifest,indent=2)+'\n')
