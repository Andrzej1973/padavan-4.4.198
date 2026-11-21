#!/usr/bin/env python3
"""Extract four hardware polling/refusal paths; inject MMIO and lock primitives."""
import argparse
from pathlib import Path

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('candidate',type=Path);p.add_argument('output',type=Path)
a=p.parse_args()
if a.output.exists():p.error('new output required')
s=(a.candidate/'hw_ctrl/cmm_asic_mt.c').read_text()
start=s.index('INT wr_iot_update_rx_wcid_checked(');end=s.index('\n}',start)+2;s=s[start:end]
blocks=[];pos=0
for i in range(4):
    begin=s.index('if (WaitCnt == 100) {',pos)
    loop=s.rfind('WaitCnt = 0;',pos,begin)
    assert loop>=0
    brace=s.index('{',begin);depth=0
    for end in range(brace,len(s)):
        if s[end]=='{':depth+=1
        elif s[end]=='}':
            depth-=1
            if depth==0:break
    block=s[loop:end+1]
    assert block.count('return WR_IOT_WCID_PARTIAL;')==1
    assert block.count('NdisReleaseSpinLock')==1
    assert ('MtAsicACQueue' in block)==(i==0)
    blocks.append(block);pos=end+1
assert 'if (WaitCnt == 100)' not in s[pos:]
prefix=r'''
#include <assert.h>
#define WR_IOT_WCID_PARTIAL -2
#define RT_DEBUG_ERROR 0
#define IU_BUSY 1
#define WTBL_OFF_WIUCR 1
#define AC_QUEUE_START 1
#define DBGPRINT(l,args) do{(void)(l);}while(0)
typedef struct {int IndirectUpdateLock;} ADAPTER;
static int held,reads,delays,restarts,clear_at;
#define RTMP_IO_READ32(a,r,v) do{(void)(a);(void)(r);reads++;*(v)=reads>=clear_at?0:IU_BUSY;}while(0)
#define RtmpusecDelay(us) do{assert((us)==50);delays++;}while(0)
#define NdisReleaseSpinLock(l) do{(void)(l);assert(held);held=0;}while(0)
#define MtAsicACQueue(a,c,i,m) do{(void)(a);(void)(i);assert((c)==AC_QUEUE_START&&(m)==15&&!held);restarts++;}while(0)
'''
functions=''
for i,block in enumerate(blocks):
    functions+=('static int poll%d(ADAPTER *pAd){unsigned char WaitCnt;unsigned int Value;int apidx=0;(void)apidx;(void)pAd;\n'%i
                +block+'\nreturn 0;}\n')
suffix=r'''
int main(void){ADAPTER a={0};int (*polls[4])(ADAPTER*)={poll0,poll1,poll2,poll3};
for(int i=0;i<4;i++){
 held=1;reads=delays=restarts=0;clear_at=101;
 assert(polls[i](&a)==-2&&reads==100&&delays==100);
#ifdef RTMP_PCI_SUPPORT
 assert(!held);assert(restarts==(i==0));
#else
 assert(held);
#endif
 held=1;reads=delays=restarts=0;clear_at=100;
 assert(polls[i](&a)==0&&reads==100&&delays==99&&held&&!restarts);
 held=1;reads=delays=restarts=0;clear_at=1;
 assert(polls[i](&a)==0&&reads==1&&!delays&&held&&!restarts);
}
return 0;}
'''
# Non-PCI first timeout restarts queues without a lock; test macro models this.
prefix=prefix.replace('assert((c)==AC_QUEUE_START&&(m)==15&&!held);','assert((c)==AC_QUEUE_START&&(m)==15);assert(held==expected_restart_lock);')
prefix=prefix.replace('static int held,reads,delays,restarts,clear_at;', '''static int held,reads,delays,restarts,clear_at;
#ifdef RTMP_PCI_SUPPORT
+static const int expected_restart_lock=0;
#else
+static const int expected_restart_lock=1;
#endif
'''.replace('\n+','\n'))
if blocks[0].index('MtAsicACQueue') < blocks[0].index('NdisReleaseSpinLock'):
    prefix=prefix.replace('expected_restart_lock=0','expected_restart_lock=1')
a.output.write_text(prefix+functions+suffix,encoding='utf-8')
print('Extracted four actual polling/timeout paths; full MMIO transaction not tested')
