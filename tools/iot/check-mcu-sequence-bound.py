#!/usr/bin/env python3
"""Exercise exact candidate exhaustion branch; not full queue concurrency."""
import argparse,subprocess,tempfile
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('candidate',type=Path);a=p.parse_args()
s=(a.candidate/'mcu/andes_core.c').read_text()
start=s.index('                if (!msg->seq) {')
end=s.index('\n            }',start)
branch=s[start:end]
assert branch.count('continue;')==1
assert s.index('AndesGetCmdMsgSeq(ad);',s.index('static INT32 AndesDequeueAndKickOutCmdMsgs'))<start<s.index('ad->chipOps.andes_fill_cmd_header',start)
cleanup_start=s.index('        if (msg->wr_iot_unsubmitted) {', s.index('/* Copy checked status before queue transfer/free.'))
cleanup_end=s.index('\n\t\tif (OS_TEST_BIT(MCU_INIT',cleanup_start)
cleanup=s[cleanup_start:cleanup_end]
assert cleanup.count('AndesForceFreeCmdMsg(msg);')==1
assert cleanup.index('return NDIS_STATUS_FAILURE;')>cleanup.index('AndesForceFreeCmdMsg(msg);')
code=r'''
#include <assert.h>
#define TRUE 1
#define NDIS_STATUS_FAILURE -1
#define tx_kickout_fail 4
struct message {unsigned seq;int wr_iot_unsubmitted,state,ack_done;};
#define RTMP_OS_COMPLETE(x) (++*(x))
static int frees;
static void AndesForceFreeCmdMsg(struct message *msg){assert(msg->wr_iot_unsubmitted);frees++;}
static int finish(struct message *msg){
'''+cleanup+r'''
return 0;}
static int dispatch(struct message *msg){int ret=0,headers=0;
for(int i=0;i<1;i++){
'''+branch+r'''
headers++;
}
assert(headers==(msg->seq!=0));return ret;}
int main(void){struct message m={0};
assert(dispatch(&m)==-1&&m.wr_iot_unsubmitted&&m.state==4&&m.ack_done==1);
assert(finish(&m)==-1&&frees==1);
for(unsigned id=1;id<=15;id++){
 m=(struct message){.seq=id};assert(dispatch(&m)==0&&!m.wr_iot_unsubmitted&&!m.ack_done);
 assert(finish(&m)==0&&frees==1);
}return 0;}
'''
with tempfile.TemporaryDirectory(prefix='wr-sequence-exhaustion-') as d:
 c=Path(d)/'check.c';c.write_text(code)
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-pie','-no-pie',str(c),'-o',d+'/check'],check=True)
 subprocess.run([d+'/check'],check=True)
print('PASS extracted exhaustion completion before header; single private-message free before queue transfer; real destructor/concurrency unproved')
