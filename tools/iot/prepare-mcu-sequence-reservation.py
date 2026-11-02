#!/usr/bin/env python3
"""Bind host ID reservations to message lifetime in isolated bounded candidate."""
import argparse,shutil,hashlib,json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
src=a.source.resolve(strict=True);out=a.output.resolve()
if out.exists() or src==out or src in out.parents or out in src.parents:p.error('new output required')
pins={'include/rtmp.h': 'a23297877ab461810633feba83497c40873552e6ba8346ba0d430ad6c35a3dc6', 'common/rtmp_init.c': '736e9a27149f04bf09267408c57278e2dfc195d5dd18fae10d62c2b80c97f1de', 'include/mcu/andes_core.h': 'c43d3b74bdf25d9adb497610677b5118cfc5ea2c819151904ecd3b6ce9ffa140', 'mcu/andes_core.c': '1303af5292b2bad761b7874a99004c47e77751861433b0a82f91bf06614cfc12', 'include/wr-iot-mcu-message-lifetime.inc': '21175ec4d3e3e65bc3da55ed8c45fb90665ceebecd6ea8940866cb827e5dc758'}
if src.with_name(src.name+'.manifest.json').exists():
 pins={'include/rtmp.h': 'aa0c3351fb21acc57c9343e4a79f29d6ced1e7dca8ebbecb338298790e8f0e96', 'common/rtmp_init.c': 'd683b789d6afc24ff44a1a21ba0e60ecc10daac4471bc01a3d83e2b1e60273a0', 'include/mcu/andes_core.h': 'f351d68aa30bd8e782cf4f6e4a2a0b9a8fbd9c283e92a464acfe29b15a5e100b', 'mcu/andes_core.c': '1303af5292b2bad761b7874a99004c47e77751861433b0a82f91bf06614cfc12', 'include/wr-iot-mcu-message-lifetime.inc': '21175ec4d3e3e65bc3da55ed8c45fb90665ceebecd6ea8940866cb827e5dc758'}
pins['include/wr-iot-mcu-sender-release.inc']='da67198c3f8aeb0f170b04274832b5ee339b85932f22ab52ff61448294c8a104'
for name,digest in pins.items():
 if hashlib.sha256((src/name).read_bytes()).hexdigest()!=digest:p.error('unreviewed input: '+name)
parent_path=src.with_name(src.name+'.manifest.json')
parent=None
if parent_path.exists():
 parent=json.loads(parent_path.read_text())
 actual={str(f.relative_to(src)):hashlib.sha256(f.read_bytes()).hexdigest() for f in src.rglob('*') if f.is_file()}
 if actual!=parent.get('merged_driver_sha256') or parent.get('production_installed') is not False:
  p.error('changed merged input or unsupported acceptance state')
changes={}
reverse=[]
def edit(name,old,new,count=1):
 s=changes.get(name,(src/name).read_text());assert s.count(old)==count,(name,old)
 changes[name]=s.replace(old,new)
 reverse.append((name,new,old,count))
edit('include/rtmp.h','#include "mcu-sender-owner.h"','#include "mcu-sender-owner.h"\n#include "mcu-sequence-reservation.h"')
edit('include/rtmp.h',' struct wr_iot_mcu_sender_owner wr_iot_mcu_sender_owner;',' struct wr_iot_mcu_sender_owner wr_iot_mcu_sender_owner;\n struct wr_iot_mcu_sequence_reservation wr_iot_sequence;')
edit('common/rtmp_init.c','wr_iot_mcu_sender_init(&pAd->wr_iot_mcu_sender_owner);','wr_iot_mcu_sender_init(&pAd->wr_iot_mcu_sender_owner);\n        memset(&pAd->wr_iot_sequence,0,sizeof(pAd->wr_iot_sequence));')
edit('include/mcu/andes_core.h','    BOOLEAN wr_iot_checked;','    unsigned int wr_iot_sequence_slot;\n    BOOLEAN wr_iot_checked;')
# Full raw allocator memset initializes slot; command reinit must retain lease.
assert (src/'mcu/andes_core.c').read_text().count('memset(msg, 0x00, sizeof(*msg));')==1
# Snapshot before freeing msg; release at final message drop under lifetime lock.
edit('mcu/andes_core.c','\tstruct MCU_CTRL *ctl = &ad->MCUCtrl;\n\n\tif (msg->need_wait)', '\tstruct MCU_CTRL *ctl = &ad->MCUCtrl;\n unsigned int wr_slot=msg->wr_iot_sequence_slot;\n\n\tif (msg->need_wait)',2)
edit('mcu/andes_core.c','wr_iot_mcu_message_drop(ad);','wr_iot_mcu_message_drop(ad,wr_slot);',2)
s=changes['mcu/andes_core.c'];start=s.index('static inline UCHAR AndesGetCmdMsgSeq(');end=s.index('\nstatic VOID _AndesQueueTailCmdMsg',start)
old_allocator=s[start:end]
s=s[:start]+'''static inline UCHAR AndesGetCmdMsgSeq(RTMP_ADAPTER *ad,struct cmd_msg *msg)
{
 unsigned long flags;
 unsigned int slot;
 RTMP_SPIN_LOCK_IRQSAVE(&ad->wr_iot_mcu_sender_lock,&flags);
 slot=msg->wr_iot_sequence_slot;
 if(slot){
  if(slot>15 || ad->wr_iot_sequence.poisoned ||
     !(ad->wr_iot_sequence.occupied&(1u<<slot))){
   ad->wr_iot_sequence.poisoned=1;
   ad->wr_iot_mcu_sender_owner.poisoned=1;
   ad->wr_iot_mcu_sender_owner.closed=1;
   slot=0;
  }
 }else{
  slot=wr_iot_mcu_sequence_reserve(&ad->wr_iot_sequence);
  msg->wr_iot_sequence_slot=slot;
 }
 RTMP_SPIN_UNLOCK_IRQRESTORE(&ad->wr_iot_mcu_sender_lock,&flags);
 return (UCHAR)slot;
}

'''+s[end:];assert s.count('AndesGetCmdMsgSeq(ad);')==1
new_allocator=s[start:s.index('\nstatic VOID _AndesQueueTailCmdMsg',start)]
reverse.append(('mcu/andes_core.c',new_allocator,old_allocator,1))
changes['mcu/andes_core.c']=s.replace('AndesGetCmdMsgSeq(ad);','AndesGetCmdMsgSeq(ad,msg);')
reverse.append(('mcu/andes_core.c','AndesGetCmdMsgSeq(ad,msg);','AndesGetCmdMsgSeq(ad);',1))
edit('include/wr-iot-mcu-message-lifetime.inc','wr_iot_mcu_message_drop(RTMP_ADAPTER *ad)','wr_iot_mcu_message_drop(RTMP_ADAPTER *ad,unsigned int slot)')
edit('include/wr-iot-mcu-message-lifetime.inc',' (void)wr_iot_mcu_message_leave', ''' if(slot && !wr_iot_mcu_sequence_release(&ad->wr_iot_sequence,slot)){
  ad->wr_iot_mcu_sender_owner.poisoned=1;
  ad->wr_iot_mcu_sender_owner.closed=1;
 }
 (void)wr_iot_mcu_message_leave''')
edit('include/wr-iot-mcu-message-lifetime.inc','wr_iot_mcu_message_drop(ad);','wr_iot_mcu_message_drop(ad,0);')
edit('include/wr-iot-mcu-sender-release.inc',
 ' serial=ad->wr_iot_mcu_sender_owner.close_serial;',
 ' /* Ledger independently gates release even if message accounting disagrees. */\n if(ad->wr_iot_sequence.occupied || ad->wr_iot_sequence.poisoned){\n  RTMP_SPIN_UNLOCK_IRQRESTORE(&ad->wr_iot_mcu_sender_lock,&flags);\n  return NDIS_STATUS_FAILURE;\n }\n serial=ad->wr_iot_mcu_sender_owner.close_serial;')
restored=dict(changes)
for name,new,old,count in reversed(reverse):
 assert restored[name].count(new)==count,(name,'reverse anchor')
 restored[name]=restored[name].replace(new,old)
for name,text in restored.items():assert text==(src/name).read_text(),name
shutil.copytree(src,out)
for name,s in changes.items():(out/name).write_text(s)
shutil.copyfile(Path(__file__).with_name('mcu-sequence-reservation.h'),out/'include/mcu-sequence-reservation.h')
out.with_name(out.name+'.reservation.json').write_text(json.dumps({'input_sha256':pins,'output_sha256':{n:hashlib.sha256((out/n).read_bytes()).hexdigest() for n in changes},'reverse_verified':True,'production_installed':False,'target_compiled':False},indent=2)+'\n')
print('Staged ID reservation until final message drop; epoch and full teardown unproved')

if parent is not None:
 merged=dict(parent)
 actual={str(f.relative_to(out)):hashlib.sha256(f.read_bytes()).hexdigest() for f in out.rglob('*') if f.is_file()}
 merged['merged_driver_sha256']=actual
 merged['candidate_driver_sha256']=dict(parent['candidate_driver_sha256'])
 for name,digest in actual.items():
  if parent['merged_driver_sha256'].get(name)!=digest:merged['candidate_driver_sha256'][name]=digest
 merged['mcu_sequence_reservation_layer']={'production_installed':False,'target_compiled':False,'runtime_verified':False}
 merged['production_installed']=False;merged['target_compiled']=False;merged['runtime_verified']=False
 out.with_name(out.name+'.manifest.json').write_text(json.dumps(merged,indent=2)+'\n')
