#!/usr/bin/env python3
"""Prepare explicit owned boot TX API; loader/tasklet binding remains unfinished."""
import argparse
import hashlib
import json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('--install-isolated',action='store_true',required=True);a=p.parse_args()
src=a.source.resolve();mp=Path(str(src)+'.manifest.json');raw=mp.read_bytes();manifest=json.loads(raw)
actual={str(f.relative_to(src)):hashlib.sha256(f.read_bytes()).hexdigest() for f in src.rglob('*') if f.is_file()}
if (manifest.get('production_installed') is not False or manifest.get('target_compiled') is not False or
    'mcu_rx_direct' not in manifest or 'mcu_boot_transport' in manifest or actual!=manifest['merged_driver_sha256']):
 p.error('Expected unchanged isolated direct-RX candidate')
names=('include/rtmp.h','include/mcu/andes_core.h','common/rtmp_init.c','mcu/andes_core.c')
changes={n:(src/n).read_text() for n in names}
def one(name,old,new):
 if changes[name].count(old)!=1:raise ValueError('Changed boot transport anchor: '+name+': '+old)
 changes[name]=changes[name].replace(old,new)
one('include/rtmp.h','#include "mcu-boot-result.h"','#include "mcu-boot-result.h"\n#include "mcu-boot-ticket.h"')
one('include/rtmp.h',' struct wr_iot_mcu_sender_owner wr_iot_mcu_sender_owner;',
    ' struct wr_iot_mcu_sender_owner wr_iot_mcu_sender_owner;\n'
    ' struct wr_iot_mcu_boot_ticket wr_iot_boot_ticket;\n unsigned int wr_iot_boot_active,wr_iot_boot_failed;')
one('common/rtmp_init.c','wr_iot_mcu_sender_init(&pAd->wr_iot_mcu_sender_owner);',
    'wr_iot_mcu_sender_init(&pAd->wr_iot_mcu_sender_owner);\n'
    '        memset(&pAd->wr_iot_boot_ticket,0,sizeof(pAd->wr_iot_boot_ticket));\n'
    '        pAd->wr_iot_boot_active=pAd->wr_iot_boot_failed=0;')
one('include/mcu/andes_core.h','    BOOLEAN wr_iot_checked;',
    '    unsigned long wr_iot_boot_peer_serial,wr_iot_boot_radio_serial,wr_iot_boot_epoch;\n    BOOLEAN wr_iot_checked;')
one('include/mcu/andes_core.h','INT32 AndesSendCmdMsg(struct _RTMP_ADAPTER *pAd, struct cmd_msg *msg);',
    'INT32 AndesSendCmdMsg(struct _RTMP_ADAPTER *pAd, struct cmd_msg *msg);\n'
    '#include "mcu-boot-ticket.h"\n#if defined(MT_MAC) && defined(RTMP_PCI_SUPPORT)\n'
    'INT32 wr_iot_mcu_boot_reserve(struct _RTMP_ADAPTER *ad,unsigned long peer_serial,struct wr_iot_mcu_boot_ticket *out);\n'
    'struct cmd_msg *wr_iot_mcu_boot_alloc(struct _RTMP_ADAPTER *ad,unsigned int length,const struct wr_iot_mcu_boot_ticket *ticket);\n'
    'INT32 wr_iot_mcu_boot_send(struct _RTMP_ADAPTER *ad,struct cmd_msg *msg,const struct wr_iot_mcu_boot_ticket *ticket);\n#endif')
one('mcu/andes_core.c','#include "wr-iot-mcu-owned-off.inc"',
    '#include "wr-iot-mcu-owned-off.inc"\n#if defined(MT_MAC) && defined(RTMP_PCI_SUPPORT)\n#include "wr-iot-mcu-boot-transport.inc"\n#endif')
for name in ('mcu-boot-ticket.h','mcu-boot-transport.inc'):
 changes['include/'+('wr-iot-'+name if name.endswith('.inc') else name)]=Path(__file__).with_name(name).read_text()
for name,text in changes.items():(src/name).write_text(text)
hashes={n:hashlib.sha256((src/n).read_bytes()).hexdigest() for n in changes}
manifest['merged_driver_sha256'].update(hashes);manifest['candidate_driver_sha256'].update(hashes)
manifest['mcu_boot_transport']={'input_manifest_sha256':hashlib.sha256(raw).hexdigest(),'output_sha256':hashes,'scope':'explicit owned boot transport API; loader and tasklet binding unfinished','target_compiled':False,'runtime_verified':False,'firmware_epoch_verified':False,'loader_bound':False}
mp.write_text(json.dumps(manifest,indent=2)+'\n')
