#!/usr/bin/env python3
"""Isolated bounded sequence exhaustion candidate; no firmware epoch proof."""
import argparse, hashlib, json, shutil
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('source',type=Path);p.add_argument('output',type=Path)
a=p.parse_args();src=a.source.resolve(strict=True);out=a.output.resolve()
if out.exists() or src==out or src in out.parents or out in src.parents:
 p.error('new separate output required')
parent_path=src.with_name(src.name+'.manifest.json')
parent=None
if parent_path.exists():
 parent=json.loads(parent_path.read_text())
 actual={str(f.relative_to(src)):hashlib.sha256(f.read_bytes()).hexdigest() for f in src.rglob('*') if f.is_file()}
 if actual!=parent.get('merged_driver_sha256') or parent.get('production_installed') is not False:
  p.error('changed merged input or unsupported acceptance state')
f=src/'mcu/andes_core.c'
if hashlib.sha256(f.read_bytes()).hexdigest() not in ('ff2802743f7e46796b9911f27dcb61aa43e7f4e26611b7934f7fc47817f9084a','27f950013ed4e33bfb8865ef39aa61fb4d2b8f57e187f9cfbd6331e31353d703'):
 p.error('unreviewed MCU source')
s=f.read_text();original=s
start=s.index('static inline UCHAR AndesGetCmdMsgSeq(')
end=s.index('\nstatic VOID _AndesQueueTailCmdMsg',start)
old=s[start:end]
assert old.count('goto get_seq;')==1
new='''#include "mcu-sequence-slot.h"
static inline UCHAR AndesGetCmdMsgSeq(RTMP_ADAPTER *ad)
{
 struct MCU_CTRL *ctl=&ad->MCUCtrl;
 struct cmd_msg *msg;
 unsigned long flags;
 unsigned int occupied=0,slot;
 RTMP_SPIN_LOCK_IRQSAVE(&ctl->ackq_lock,&flags);
 DlListForEach(msg,&ctl->ackq,struct cmd_msg,list) {
  if(msg->seq>=1 && msg->seq<=15)occupied|=1u<<msg->seq;
 }
 slot=wr_iot_mcu_sequence_slot(ctl->cmd_seq,occupied);
 if(slot)ctl->cmd_seq=slot;
 RTMP_SPIN_UNLOCK_IRQRESTORE(&ctl->ackq_lock,&flags);
 return (UCHAR)slot;
}

'''
s=s[:start]+new+s[end:]
anchor='\t\t\t\tmsg->seq = AndesGetCmdMsgSeq(ad);'
assert s.count(anchor)==1
s=s.replace(anchor,'''            {
                msg->seq = AndesGetCmdMsgSeq(ad);
                if (!msg->seq) {
                    msg->wr_iot_unsubmitted = TRUE;
                    msg->state = tx_kickout_fail;
                    RTMP_OS_COMPLETE(&msg->ack_done);
                    ret = NDIS_STATUS_FAILURE;
                    continue;
                }
            }''')
anchor='\t\t\tif (msg->state == tx_kickout_fail) {'
assert s.count(anchor)==1
s=s.replace(anchor,anchor+'\n                ret = NDIS_STATUS_FAILURE;')
anchor='if (msg->wr_iot_checked && msg->wr_iot_unsubmitted) {'
assert s.count(anchor)==1
s=s.replace(anchor,'if (msg->wr_iot_unsubmitted) {')
shutil.copytree(src,out)
(out/'mcu/andes_core.c').write_text(s)
shutil.copyfile(Path(__file__).with_name('mcu-sequence-slot.h'),out/'include/mcu-sequence-slot.h')
r={'input_sha256':hashlib.sha256(original.encode()).hexdigest(),'output_sha256':hashlib.sha256(s.encode()).hexdigest(),'production_installed':False,'target_compiled':False,'runtime_verified':False,'limitations':['slot is selected, not atomically reserved through ACK insertion','firmware sequence freshness unproved']}
out.with_name(out.name+'.sequence-bound.json').write_text(json.dumps(r,indent=2)+'\n')
print('Staged bounded search and pre-submit exhaustion failure; reservation/freshness unproved')

if parent is not None:
 merged=dict(parent)
 actual={str(f.relative_to(out)):hashlib.sha256(f.read_bytes()).hexdigest() for f in out.rglob('*') if f.is_file()}
 merged['merged_driver_sha256']=actual
 merged['candidate_driver_sha256']=dict(parent['candidate_driver_sha256'])
 for name,digest in actual.items():
  if parent['merged_driver_sha256'].get(name)!=digest:merged['candidate_driver_sha256'][name]=digest
 merged['mcu_sequence_bound_layer']={'production_installed':False,'target_compiled':False,'runtime_verified':False}
 merged['production_installed']=False;merged['target_compiled']=False;merged['runtime_verified']=False
 out.with_name(out.name+'.manifest.json').write_text(json.dumps(merged,indent=2)+'\n')
