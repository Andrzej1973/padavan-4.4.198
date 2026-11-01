#!/usr/bin/env python3
"""Verify sender source transformation; does not accept teardown or lifetime."""
import argparse,hashlib,json,subprocess,tempfile
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('candidate',type=Path);a=p.parse_args()
here=Path(__file__).resolve().parent
for local,target in [('mcu-sender-owner.h','mcu-sender-owner.h'),('mcu-sender-wrapper.inc','wr-iot-mcu-sender-wrapper.inc'),('mcu-sender-drain.inc','wr-iot-mcu-sender-drain.inc')]:
 assert (here/local).read_bytes()==(a.candidate/'include'/target).read_bytes(),target
old=(a.source/'mcu/andes_core.c').read_text();new=(a.candidate/'mcu/andes_core.c').read_text()
public='INT32 AndesSendCmdMsg(PRTMP_ADAPTER ad, struct cmd_msg *msg)'
private='static INT32 wr_iot_mcu_send_body(PRTMP_ADAPTER ad, struct cmd_msg *msg)'
include='\n#include "wr-iot-mcu-sender-wrapper.inc"\n#include "wr-iot-mcu-sender-drain.inc"\n'
assert new.count(private)==1 and new.count(include)==1
assert new.replace(private,public,1).replace(include,'',1)==old,'transport changed beyond wrapper binding'
init=(a.candidate/'common/rtmp_init.c').read_text()
assert init.count('wr_iot_mcu_sender_init(&pAd->wr_iot_mcu_sender_owner)')==1
assert init.index('wr_iot_mcu_sender_init(')<init.index('Status = RTMPAllocTxRxRingMemory(pAd);')
receipt=json.loads(a.candidate.with_name(a.candidate.name+'.sender-binding.json').read_text())
for name,digest in receipt['output_sha256'].items():
 assert hashlib.sha256((a.candidate/name).read_bytes()).hexdigest()==digest,name
assert receipt['production_installed'] is False and receipt['target_compiled'] is False
# Execute exact generated unwind statements with fault checkpoints.
cleanup='if(wr_sender_lock_initialized) NdisFreeSpinLock(&pAd->wr_iot_mcu_sender_lock);'
assert init.count(cleanup)==1
assert init.index(cleanup)<init.index('RtmpOsVfree(pAd);',init.index(cleanup))
code=r"""
#include <assert.h>
struct adapter {int wr_iot_mcu_sender_lock;};
static int freed,locks;
#define NdisFreeSpinLock(p) do{assert(!freed);(void)(p);locks++;}while(0)
#define RtmpOsVfree(p) do{assert(p);freed++;}while(0)
static void unwind(struct adapter *pAd,int wr_sender_lock_initialized){
"""+cleanup+'\nRtmpOsVfree(pAd);\n}'+r"""
int main(void){struct adapter a={0};
for(int stage=0;stage<3;stage++){
 freed=locks=0;unwind(&a,stage!=0);
 assert(freed==1&&locks==(stage!=0));
}return 0;}
"""
with tempfile.TemporaryDirectory(prefix='wr-mcu-unwind-') as t:
 c=Path(t)/'check.c';exe=Path(t)/'check';c.write_text(code)
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined',str(c),'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)
print('PASS extracted sender-lock unwind ordering before/after initialization; OS_ABL allocation failure remains unproved')
print('PASS exact sender body preservation, helper identity, pre-ring init and receipt hashes; release/publication unproved')
