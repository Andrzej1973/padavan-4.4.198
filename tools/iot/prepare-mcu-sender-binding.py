#!/usr/bin/env python3
"""Stage MCU sender source binding; release/close gates unbound, never install."""
import argparse, hashlib, json, shutil
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('output',type=Path)
a=p.parse_args();src=a.source.resolve(strict=True);out=a.output.resolve()
if out.exists() or src==out or src in out.parents or out in src.parents:p.error('new separate output required')
pins={'include/rtmp.h': 'bde083b8a2eaa481564e3b480b91d1c438e2901356065f37e3963c5fec9e32d3', 'common/rtmp_init.c': 'ca7e4f406d568bb04ede9245c5ba8f50d130f3e79918a7732811b991d6e638e3', 'mcu/andes_core.c': 'dace085882a8097080b479a37b459dc799724831eece5da16efa41f21370f9a3'}
texts={}
for n,h in pins.items():
 raw=(src/n).read_bytes()
 if hashlib.sha256(raw).hexdigest()!=h:p.error('unreviewed source: '+n)
 texts[n]=raw.decode()
def one(n,old,new):
 if texts[n].count(old)!=1:p.error('changed anchor: '+n)
 texts[n]=texts[n].replace(old,new,1)
one('include/rtmp.h','#include "radio-transition.h"','#include "radio-transition.h"\n#include "mcu-sender-owner.h"')
one('include/rtmp.h','\tNDIS_SPIN_LOCK wr_iot_transition_lock;',
 ' NDIS_SPIN_LOCK wr_iot_mcu_sender_lock;\n wait_queue_head_t wr_iot_mcu_sender_wait;\n struct wr_iot_mcu_sender_owner wr_iot_mcu_sender_owner;\n\tNDIS_SPIN_LOCK wr_iot_transition_lock;')
one('common/rtmp_init.c','\t\tNdisAllocateSpinLock(pAd, &pAd->MgmtRingLock);',
 '        wr_iot_mcu_sender_init(&pAd->wr_iot_mcu_sender_owner);\n        NdisAllocateSpinLock(pAd, &pAd->wr_iot_mcu_sender_lock);\n        init_waitqueue_head(&pAd->wr_iot_mcu_sender_wait);\n\t\tNdisAllocateSpinLock(pAd, &pAd->MgmtRingLock);')
one('common/rtmp_init.c','NDIS_STATUS RTMPAllocAdapterBlock(VOID *handle, VOID **ppAdapter)\n{',
 'NDIS_STATUS RTMPAllocAdapterBlock(VOID *handle, VOID **ppAdapter)\n{\n int wr_sender_lock_initialized=0;')
one('common/rtmp_init.c','        init_waitqueue_head(&pAd->wr_iot_mcu_sender_wait);',
 '        init_waitqueue_head(&pAd->wr_iot_mcu_sender_wait);\n        wr_sender_lock_initialized=1;')
one('common/rtmp_init.c','\t\t\tRtmpOsVfree(pAd);',
 '\t\t\tif(wr_sender_lock_initialized) NdisFreeSpinLock(&pAd->wr_iot_mcu_sender_lock);\n\t\t\tRtmpOsVfree(pAd);')
n='mcu/andes_core.c';sig='INT32 AndesSendCmdMsg(PRTMP_ADAPTER ad, struct cmd_msg *msg)'
one(n,sig,'static INT32 wr_iot_mcu_send_body(PRTMP_ADAPTER ad, struct cmd_msg *msg)')
start=texts[n].index('static INT32 wr_iot_mcu_send_body(');end=texts[n].index('\n}',start)+2
texts[n]=texts[n][:end]+'\n#include "wr-iot-mcu-sender-wrapper.inc"\n#include "wr-iot-mcu-sender-drain.inc"\n'+texts[n][end:]
shutil.copytree(src,out)
for n,t in texts.items():(out/n).write_text(t)
for local,target in [('mcu-sender-owner.h','mcu-sender-owner.h'),('mcu-sender-wrapper.inc','wr-iot-mcu-sender-wrapper.inc'),('mcu-sender-drain.inc','wr-iot-mcu-sender-drain.inc')]:
 shutil.copyfile(Path(__file__).with_name(local),out/'include'/target)
r={'scope':'normal sender source binding only; no close/drain/release or lock destruction binding; DO NOT INSTALL','input_sha256':pins,'output_sha256':{n:hashlib.sha256((out/n).read_bytes()).hexdigest() for n in pins},'production_installed':False,'target_compiled':False,'runtime_verified':False}
out.with_name(out.name+'.sender-binding.json').write_text(json.dumps(r,indent=2)+'\n')
print('Staged sender binding; close and every adapter release path remain mandatory before use')
