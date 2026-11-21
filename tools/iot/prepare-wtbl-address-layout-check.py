#!/usr/bin/env python3
"""Extract vendor little-endian address unions; host layout check, not MIPS ABI."""
import argparse
from pathlib import Path

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('candidate',type=Path);p.add_argument('output',type=Path)
a=p.parse_args()
if a.output.exists():p.error('new output required')
s=(a.candidate/'include/mac/mac_mt/wf_wtblon.h').read_text()
start=s.index('#ifdef RT_BIG_ENDIAN\nunion WTBL_1_DW0')
end=s.index('#endif',start)+len('#endif')
dw0=s[start:end]
start=s.index('union WTBL_1_DW1 {',end);end=s.index('\n};',start)+3
dw1=s[start:end]
prefix='#include <assert.h>\n#include <stdint.h>\ntypedef uint32_t UINT32;\n'
suffix=r'''
_Static_assert(sizeof(union WTBL_1_DW0)==4,"DW0 width");
_Static_assert(sizeof(union WTBL_1_DW1)==4,"DW1 width");
int main(void){
 union WTBL_1_DW0 a={0};union WTBL_1_DW1 b={0};
 a.field.addr_4=0x5a;a.field.addr_5=0xa5;
 assert((a.word&0xffffU)==0xa55aU);
 a.word=0;a.field.rv=a.field.rc_a2=1;
 assert(!(a.word&0xffffU));
 b.field.addr_0=0x12345678U;assert(b.word==0x12345678U);
 /* Every address bit is visible; unrelated status bits are excluded. */
 for(unsigned int i=0;i<16;i++){a.word=1U<<i;assert(a.field.addr_4||a.field.addr_5);}
 for(unsigned int i=16;i<32;i++){a.word=1U<<i;assert(!a.field.addr_4&&!a.field.addr_5);}
 return 0;}
'''
a.output.write_text(prefix+dw0+'\n'+dw1+suffix,encoding='utf-8')
print('Extracted actual WTBL DW0/DW1 unions; little-endian host layout only')
