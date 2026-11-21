#!/usr/bin/env python3
"""Stage MCU sender source binding; release/close gates unbound, never install."""
import argparse, hashlib, json, shutil
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('output',type=Path)
a=p.parse_args();src=a.source.resolve(strict=True);out=a.output.resolve()
if out.exists() or src==out or src in out.parents or out in src.parents:p.error('new separate output required')
pins={'include/rtmp.h': 'bde083b8a2eaa481564e3b480b91d1c438e2901356065f37e3963c5fec9e32d3', 'common/rtmp_init.c': 'ca7e4f406d568bb04ede9245c5ba8f50d130f3e79918a7732811b991d6e638e3', 'mcu/andes_core.c': 'dace085882a8097080b479a37b459dc799724831eece5da16efa41f21370f9a3'}
pins['os/linux/rt_profile.c']='f7947cff4fc76f9e14e0dd47d08d653d7189f1766fdc3be0ff1547f82b89a521'
parent_path=src.with_name(src.name+'.manifest.json')
parent=None
if parent_path.exists():
 parent=json.loads(parent_path.read_text())
 actual={str(f.relative_to(src)):hashlib.sha256(f.read_bytes()).hexdigest() for f in src.rglob('*') if f.is_file()}
 if actual!=parent.get('merged_driver_sha256') or parent.get('production_installed') is not False:
  p.error('changed merged input or unsupported acceptance state')
 pins={'include/rtmp.h': '8739ed3ebd9d7b715074d5ea13add1ab5b0ba4a8b5383889eac8dcdd5490b2c7', 'common/rtmp_init.c': '28da09524ff7712a3b2a6d2331ba901889509224f6fdd329b343ed071495e8c6', 'mcu/andes_core.c': '1d9d162dbe8e9ca782979977dd0d89f993d5126348d7b36600f20c45b87d65ff', 'os/linux/rt_profile.c': '3e45b968dd13082076bb238b4fa0bf52681cb7576e680f4bafe24d0f1f5c691c'}
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
n='mcu/andes_core.c'
one(n,'struct cmd_msg *AndesAllocCmdMsg(RTMP_ADAPTER *ad, unsigned int length)',
 'static struct cmd_msg *wr_iot_mcu_alloc_body(RTMP_ADAPTER *ad, unsigned int length)')
start=texts[n].index('static struct cmd_msg *wr_iot_mcu_alloc_body(');end=texts[n].index('\n}',start)+2
texts[n]=texts[n][:end]+'\n#include "wr-iot-mcu-message-lifetime.inc"\n'+texts[n][end:]
# Both actual destructors update MCU counters after freeing msg. Drop the
# message lease only after that last adapter access, never inspect freed msg.
for sig in ['VOID AndesFreeCmdMsg(struct cmd_msg *msg)','VOID AndesForceFreeCmdMsg(struct cmd_msg *msg)']:
 start=texts[n].index(sig);end=texts[n].index('\n}',start)+2
 body=texts[n][start:end];old='\tctl->free_cmd_msg++;'
 if body.count(old)!=1:p.error('changed destructor counter: '+sig)
 body=body.replace(old,old+'\n wr_iot_mcu_message_drop(ad);',1)
 texts[n]=texts[n][:start]+body+texts[n][end:]
n='mcu/andes_core.c';sig='INT32 AndesSendCmdMsg(PRTMP_ADAPTER ad, struct cmd_msg *msg)'
one(n,sig,'static INT32 wr_iot_mcu_send_body(PRTMP_ADAPTER ad, struct cmd_msg *msg)')
start=texts[n].index('static INT32 wr_iot_mcu_send_body(');end=texts[n].index('\n}',start)+2
texts[n]=texts[n][:end]+'\n#include "wr-iot-mcu-sender-wrapper.inc"\n#include "wr-iot-mcu-sender-drain.inc"\n#include "wr-iot-mcu-sender-release.inc"\n'+texts[n][end:]
one('include/rtmp.h','INT wr_iot_command_task_exit_checked(RTMP_ADAPTER *pAd);',
 'INT wr_iot_command_task_exit_checked(RTMP_ADAPTER *pAd);\nINT wr_iot_mcu_sender_release_begin(RTMP_ADAPTER *ad);')
one('common/rtmp_init.c','\tif (!wr_iot_adapter_release_begin(pAd)) return FALSE;',
 '\tif (wr_iot_mcu_sender_release_begin(pAd)!=NDIS_STATUS_SUCCESS) return FALSE;\n\tif (!wr_iot_adapter_release_begin(pAd)) return FALSE;')
one('os/linux/rt_profile.c','\tos_cookie=(POS_COOKIE)pAd->OS_Cookie;',
 '\tif (wr_iot_mcu_sender_release_begin(pAd)!=NDIS_STATUS_SUCCESS) return FALSE;\n\tos_cookie=(POS_COOKIE)pAd->OS_Cookie;')
one('os/linux/rt_profile.c','\tNdisFreeSpinLock(&pAd->MgmtRingLock);',
 '\tNdisFreeSpinLock(&pAd->wr_iot_mcu_sender_lock);\n\tNdisFreeSpinLock(&pAd->MgmtRingLock);')
shutil.copytree(src,out)
for n,t in texts.items():(out/n).write_text(t)
for local,target in [('mcu-sender-owner.h','mcu-sender-owner.h'),('mcu-sender-wrapper.inc','wr-iot-mcu-sender-wrapper.inc'),('mcu-sender-drain.inc','wr-iot-mcu-sender-drain.inc'),('mcu-message-lifetime.inc','wr-iot-mcu-message-lifetime.inc'),('mcu-sender-release.inc','wr-iot-mcu-sender-release.inc')]:
 shutil.copyfile(Path(__file__).with_name(local),out/'include'/target)
r={'scope':'isolated sender/message source binding and software release gates; shutdown/owned OFF and external lifetime unproved; DO NOT INSTALL','input_sha256':pins,'output_sha256':{n:hashlib.sha256((out/n).read_bytes()).hexdigest() for n in pins},'production_installed':False,'target_compiled':False,'runtime_verified':False}
if parent is not None:
 merged=dict(parent)
 actual={str(f.relative_to(out)):hashlib.sha256(f.read_bytes()).hexdigest() for f in out.rglob('*') if f.is_file()}
 merged['merged_driver_sha256']=actual
 merged['candidate_driver_sha256']=dict(parent['candidate_driver_sha256'])
 for n,h in actual.items():
  if parent['merged_driver_sha256'].get(n)!=h:merged['candidate_driver_sha256'][n]=h
 merged['mcu_sender_layer']=r
 merged['target_compiled']=False;merged['production_installed']=False;merged['runtime_verified']=False
 out.with_name(out.name+'.manifest.json').write_text(json.dumps(merged,indent=2)+'\n')
out.with_name(out.name+'.sender-binding.json').write_text(json.dumps(r,indent=2)+'\n')
print('Staged sender/message binding and software release gates; external retirement, IRQ/DMA and shutdown remain unproved')
