#!/usr/bin/env python3
"""Bind bootstrap reserve-before-IRQ and checked failure release; no success commit."""
import argparse
import hashlib
import json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('--install-isolated',action='store_true',required=True);a=p.parse_args()
src=a.source.resolve();mp=Path(str(src)+'.manifest.json');raw=mp.read_bytes();manifest=json.loads(raw)
actual={str(f.relative_to(src)):hashlib.sha256(f.read_bytes()).hexdigest() for f in src.rglob('*') if f.is_file()}
if (manifest.get('production_installed') is not False or manifest.get('target_compiled') is not False or
    'mcu_nettask_bootstrap' not in manifest or 'mcu_boot_open' in manifest or actual!=manifest['merged_driver_sha256']):
 p.error('Expected unchanged isolated MCU-nettask bootstrap candidate')
names=('include/peer-open-request.h','include/wr-iot-peer-open-dispatch.inc','include/rtmp.h','common/rtmp_init_inf.c','os/linux/rt_main_dev.c')
changes={n:(src/n).read_text() for n in names}
def one(name,old,new):
 if changes[name].count(old)!=1:raise ValueError('Changed boot-open anchor: '+name+': '+old)
 changes[name]=changes[name].replace(old,new)
one('include/peer-open-request.h','WR_PEER_OPEN_DONE,WR_PEER_OPEN_FAIL,WR_PEER_OPEN_CONFIG_CHECK};',
    'WR_PEER_OPEN_DONE,WR_PEER_OPEN_FAIL,WR_PEER_OPEN_CONFIG_CHECK,\n WR_PEER_OPEN_BOOT_PREPARE,WR_PEER_OPEN_BOOT_IRQ_READY};')
one('include/wr-iot-peer-open-dispatch.inc',' ticket.device=request->device;ticket.serial=request->serial;',
    ' if(request->action==WR_PEER_OPEN_BOOT_PREPARE || request->action==WR_PEER_OPEN_BOOT_IRQ_READY){\n'
    '  if(request->device!=pAd->net_dev)return NDIS_STATUS_FAILURE;\n'
    '  return request->action==WR_PEER_OPEN_BOOT_PREPARE ?\n'
    '   wr_iot_boot_open_prepare(pAd,request->serial):wr_iot_boot_open_irq_ready(pAd,request->serial);\n }\n'
    ' ticket.device=request->device;ticket.serial=request->serial;')
one('include/rtmp.h','INT RtmpNetTaskExit(RTMP_ADAPTER *pAd);',
    'INT RtmpNetTaskExit(RTMP_ADAPTER *pAd);\n'
    'INT wr_iot_boot_open_prepare(RTMP_ADAPTER *ad,unsigned long serial);\n'
    'INT wr_iot_boot_open_irq_ready(RTMP_ADAPTER *ad,unsigned long serial);')
one('common/rtmp_init_inf.c','#include "wr-iot-mcu-dma-disabled-idle.inc"\n#endif', '#include "wr-iot-mcu-dma-disabled-idle.inc"\n#endif\n#include "wr-iot-mcu-boot-open.inc"')
one('common/rtmp_init_inf.c','if (MCUSysInit(pAd) != NDIS_STATUS_SUCCESS)\n\t\tgoto err6;',
    'if (MCUSysInit(pAd) != NDIS_STATUS_SUCCESS)\n\t\tgoto err6;\n'
    '#if defined(MT7603) && defined(RTMP_PCI_SUPPORT)\n'
    ' /* Until a ROM/RX/ring epoch commit is bound, never publish boot success. */\n'
    ' if(pAd->wr_iot_boot_active)goto err6;\n#endif')
net='os/linux/rt_main_dev.c';start=changes[net].index('int rt28xx_open(VOID *dev)\n{');end=changes[net].index('\n}',start)+2;body=changes[net][start:end]
def change(old,new):
 global body
 if body.count(old)!=1:raise ValueError('Changed rt28xx_open: '+old)
 body=body.replace(old,new)
change('\tint retval = 0;', '\tint retval = 0;\n int wr_irq_acquired=0,wr_irq_ready;')
anchor=' if(wr_iot_peer_open_call(pAd,&wr_claim,WR_PEER_OPEN_BEGIN)!=NDIS_STATUS_SUCCESS)return -EBUSY;'
change(anchor,anchor+'\n if(wr_iot_peer_open_call(pAd,&wr_claim,WR_PEER_OPEN_BOOT_PREPARE)!=NDIS_STATUS_SUCCESS)goto err;')
change('\tRtmpOSIRQRequest(net_dev);', '\tretval=RtmpOSIRQRequest(net_dev);\n if(retval)goto err;\n wr_irq_acquired=1;')
change('err:\n (void)wr_iot_peer_open_call(pAd,&wr_claim,WR_PEER_OPEN_FAIL);\n\tRTMP_DRIVER_IRQ_RELEASE(pAd);',
    'err:\n wr_irq_ready=wr_iot_peer_open_call(pAd,&wr_claim,WR_PEER_OPEN_BOOT_IRQ_READY);\n'
    ' (void)wr_iot_peer_open_call(pAd,&wr_claim,WR_PEER_OPEN_FAIL);\n'
    ' if(wr_irq_acquired && wr_irq_ready==NDIS_STATUS_SUCCESS)RTMP_DRIVER_IRQ_RELEASE(pAd);')
changes[net]=changes[net][:start]+body+changes[net][end:]
changes['include/wr-iot-mcu-boot-open.inc']=Path(__file__).with_name('mcu-boot-open.inc').read_text()
for name,value in changes.items():(src/name).write_text(value)
hashes={n:hashlib.sha256((src/n).read_bytes()).hexdigest() for n in changes}
manifest['merged_driver_sha256'].update(hashes);manifest['candidate_driver_sha256'].update(hashes)
manifest['mcu_boot_open']={'input_manifest_sha256':hashlib.sha256(raw).hexdigest(),'output_sha256':hashes,'scope':'reserve before IRQ, failed-init IRQ lifetime gate; successful reopen remains refused','target_compiled':False,'runtime_verified':False,'boot_success_publication':False}
mp.write_text(json.dumps(manifest,indent=2)+'\n')
