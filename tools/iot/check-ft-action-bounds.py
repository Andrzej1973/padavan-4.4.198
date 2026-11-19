#!/usr/bin/env python3
"""Check FT outer lengths against the exact vendor action-header declaration."""
import argparse,subprocess,tempfile
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);a=p.parse_args()
here=Path(__file__).resolve().parent
s=(a.source/'include/dot11r_ft.h').read_text(encoding='latin-1');start=s.index('typedef struct GNU_PACKED __FT_ACTION')
layout=s[start:s.index('} FT_ACTION, *PFT_ACTION;',start)+len('} FT_ACTION, *PFT_ACTION;')]
code='''#include <assert.h>
#include <stddef.h>
#include <limits.h>
typedef unsigned char UINT8;
#define GNU_PACKED __attribute__((packed))
#define MAC_ADDR_LEN 6
#include "ft-action-bounds.h"
'''+layout+'''
int main(void){
 unsigned short length=123;unsigned long header=offsetof(FT_ACTION,Oct);
 assert(header==14&&sizeof(FT_ACTION)==14);
 for(unsigned long size=0;size<=256;size++){
  length=123;
  int ok=wr_iot_ft_action_payload_length(size,256,24,header,&length);
  assert(ok==(size>=38));
  if(ok)assert(length==size-38);else assert(length==123);
 }
 assert(!wr_iot_ft_action_payload_length(257,256,24,header,&length));
 assert(!wr_iot_ft_action_payload_length(ULONG_MAX,ULONG_MAX,24,header,&length));
 assert(!wr_iot_ft_action_payload_length(38,256,24,header,NULL));
 assert(wr_iot_ft_action_payload_length(24+65535,ULONG_MAX,24,header,&length));
 assert(length==65535-14);
 assert(!wr_iot_ft_action_payload_length(24+65536,ULONG_MAX,24,header,&length));
 /* Both 32-bit target and 64-bit host pointer sizes differ from the header. */
 assert(4!=header&&8!=header);return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='wr-ft-bounds-') as td:
 src=Path(td)/'check.c';exe=Path(td)/'check';src.write_text(code)
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(src),'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)
print('Vendor FT header14: outer buffer, truncated/empty payload, UINT16 and overflow boundaries PASS; IE parser/driver binding unverified')
