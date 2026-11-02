#!/usr/bin/env python3
"""Exercise exact generated allocator with injected lifetime lock."""
import argparse,subprocess,tempfile
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('candidate',type=Path);a=p.parse_args();here=Path(__file__).resolve().parent
s=(a.candidate/'mcu/andes_core.c').read_text();start=s.index('static inline UCHAR AndesGetCmdMsgSeq(');end=s.index('\nstatic VOID _AndesQueueTailCmdMsg',start);fn=s[start:end]
init=s[s.index('VOID AndesInitCmdMsg('):s.index('VOID AndesAppendCmdMsg(')]
assert 'wr_iot_sequence_slot' not in init,'command initialization loses reservation'
assert s.count('memset(msg, 0x00, sizeof(*msg));')==1
code=r'''
#include "mcu-sender-owner.h"
#include "mcu-sequence-reservation.h"
#include <assert.h>
typedef unsigned char UCHAR;
struct cmd_msg {unsigned int wr_iot_sequence_slot;};
typedef struct {int wr_iot_mcu_sender_lock;struct wr_iot_mcu_sequence_reservation wr_iot_sequence;struct wr_iot_mcu_sender_owner wr_iot_mcu_sender_owner;} RTMP_ADAPTER;
static int held;
#define RTMP_SPIN_LOCK_IRQSAVE(l,f) do{(void)(l);*(f)=0;assert(!held);held=1;}while(0)
#define RTMP_SPIN_UNLOCK_IRQRESTORE(l,f) do{(void)(l);(void)(f);assert(held);held=0;}while(0)
'''+fn+r'''
int main(void){
 RTMP_ADAPTER a={0};struct cmd_msg messages[16]={{0}};
 for(unsigned i=0;i<15;i++){
  unsigned id=AndesGetCmdMsgSeq(&a,&messages[i]);assert(id==i+1&&!held);
  unsigned occupied=a.wr_iot_sequence.occupied;
  assert(AndesGetCmdMsgSeq(&a,&messages[i])==id);
  assert(a.wr_iot_sequence.occupied==occupied&&!held);
 }
 assert(!AndesGetCmdMsgSeq(&a,&messages[15])&&!messages[15].wr_iot_sequence_slot&&!held);
 a.wr_iot_sequence.occupied&=~(1u<<messages[0].wr_iot_sequence_slot);
 assert(!AndesGetCmdMsgSeq(&a,&messages[0]));
 assert(a.wr_iot_sequence.poisoned&&a.wr_iot_mcu_sender_owner.poisoned&&a.wr_iot_mcu_sender_owner.closed);
 assert(messages[0].wr_iot_sequence_slot==1&&!held);
 a=(RTMP_ADAPTER){0};messages[0].wr_iot_sequence_slot=32;
 assert(!AndesGetCmdMsgSeq(&a,&messages[0])&&a.wr_iot_sequence.poisoned&&!held);
 return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='wr-sequence-allocator-') as d:
 c=Path(d)/'check.c';c.write_text(code)
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(c),'-o',d+'/check'],check=True)
 subprocess.run([d+'/check'],check=True)
print('PASS actual allocator reserve/reentry/exhaustion/corruption and init preservation; real concurrency unproved')
