#!/usr/bin/env python3
"""Execute actual stale-event retirement with immediate slot-reuse actor."""
import subprocess,tempfile
from pathlib import Path
here=Path(__file__).resolve().parent
text=(here/'assoc-generation-kernel.h').read_text();start=text.index('static inline void wr_assoc_retire_stale_elem(')
helper=text[start:text.index('\n}',start)+2]
prefix=r'''
#include <assert.h>
typedef struct {unsigned int MsgLen;int Occupied;} MLME_QUEUE_ELEM;
#define FALSE 0
static unsigned int barriers,publications;
static void reuse(MLME_QUEUE_ELEM *elem){
 assert(!elem->Occupied&&elem->MsgLen==0&&barriers==1);
 publications++;elem->MsgLen=99;elem->Occupied=1;
}
#define smp_wmb() do{barriers++;}while(0)
#define WRITE_ONCE(field,value) do{(field)=(value);reuse(elem);}while(0)
'''
main='\nint main(void){MLME_QUEUE_ELEM elem={42,1};wr_assoc_retire_stale_elem(&elem);assert(publications==1&&elem.Occupied==1&&elem.MsgLen==99);return 0;}\n'
# The mutation releases the slot while old metadata is still present.
mutant=helper.replace(' elem->MsgLen=0;\n smp_wmb();\n WRITE_ONCE(elem->Occupied,FALSE);',' smp_wmb();\n WRITE_ONCE(elem->Occupied,FALSE);\n elem->MsgLen=0;')
assert mutant!=helper
with tempfile.TemporaryDirectory(prefix='wr-stale-retire-') as td:
 root=Path(td)
 for name,body in [('good',helper),('mutant',mutant)]:
  src=root/(name+'.c');exe=root/name;src.write_text(prefix+body+main)
  subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie',str(src),'-o',str(exe)],check=True)
  result=subprocess.run([str(exe)],capture_output=True,text=True)
  assert (result.returncode==0)==(name=='good')
  if name=='mutant':assert 'Assertion' in result.stderr
print('Stale element retirement: metadata before FREE, immediate reuse retained; wrong-order mutant rejected PASS')
