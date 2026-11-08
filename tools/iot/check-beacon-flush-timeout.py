#!/usr/bin/env python3
"""Execute vendor flush tail with MMIO stubs; show timeout is not CLOSE proof."""
from pathlib import Path
import argparse,subprocess,tempfile
p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);a=p.parse_args()
s=a.source.read_text();start='\tif (apidx > 0)\n\t\tval = val | (1 << (apidx+15));'
end='\tpMbss->bcn_buf.bcn_state = BCN_TX_IDLE;'
# Choose flush tail whose following section contains the actual queue command.
starts=[i for i in range(len(s)) if s.startswith(start,i)]
starts=[i for i in starts if '/* Flush Beacon Queue */' in s[i:i+180]]
assert len(starts)==1
first=starts[0];last=s.index(end,first)+len(end);tail=s[first:last]
code=r'''
#include <assert.h>
#include <stdio.h>
#define ARB_BCNQCR1 1U
#define ARB_BCNQCR0 2U
#define BCN_TX_IDLE 0
#define DBGPRINT(level,args) do{(void)(level);}while(0)
#define RT_DEBUG_ERROR 0
#define printk(...) do{timeouts++;}while(0)
typedef unsigned UINT32;
struct adapter {int unused;};
struct bss {struct {int bcn_state;}bcn_buf;};
static unsigned mode,waits,timeouts,writes,flush_mask,filter_command,restart_mask;
static void write32(struct adapter *ad,unsigned reg,unsigned value){(void)ad;writes++;if(reg==1)flush_mask=value;else if(reg==2)restart_mask=value;else {assert(reg==0x21c08);filter_command=value;}}
static unsigned read32(unsigned reg){if(reg==1)return mode==1||mode==3?flush_mask:0;if(reg==0x21c08)return mode==2||mode==3?0x80000000U:0;return 0;}
#define RTMP_IO_WRITE32(ad,reg,value) write32(ad,reg,value)
#define RTMP_IO_READ32(ad,reg,out) do{(void)(ad);*(out)=read32(reg);}while(0)
#define OS_WAIT(n) do{assert((n)==1);waits++;}while(0)
static void set_get_fid(struct adapter *ad,const char *s){(void)ad;assert(s[0]=='7');}
static void actual_tail(struct adapter *pAd,unsigned apidx,struct bss *pMbss){UINT32 val=0,temp=0;int j=0;
'''+tail+r'''
}
int main(void){
 for(mode=0;mode<4;mode++){
  struct adapter ad={0};struct bss b={.bcn_buf.bcn_state=3};
  waits=timeouts=writes=0;actual_tail(&ad,2,&b);
  assert(flush_mask==(1U<<17));assert(filter_command==0xa8c71200U);
  assert(writes==3&&restart_mask==(1U<<17)&&b.bcn_buf.bcn_state==BCN_TX_IDLE);
  assert(timeouts==(unsigned)((mode==1||mode==3)+(mode==2||mode==3)));
  assert(waits==1001*timeouts);
 }
 puts("PASS actual vendor flush tail: either/both timeout paths continue to re-enable BSS and IDLE; not a checked CLOSE/FIFO/late-TxS receipt");
}
'''
with tempfile.TemporaryDirectory(prefix='wr-beacon-flush-') as d:
 src=Path(d)/'test.c';out=Path(d)/'test';src.write_text(code)
 subprocess.run(['gcc','-O2','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-pie','-no-pie',str(src),'-o',str(out)],check=True)
 subprocess.run([str(out)],check=True)
