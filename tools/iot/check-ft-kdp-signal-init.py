#!/usr/bin/env python3
"""Execute generated event initialization with actual packed signal layout."""
import argparse,re,runpy,subprocess,tempfile
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('source',type=Path);a=p.parse_args();here=Path(__file__).resolve().parent
header=(a.source/'include/ft.h').read_text()
start=header.index('typedef struct GNU_PACKED _RT_SIGNAL_STRUC {')
end=header.index('} RT_SIGNAL_STRUC, *PRT_SIGNAL_STRUC;',start)+len('} RT_SIGNAL_STRUC, *PRT_SIGNAL_STRUC;')
declaration=header[start:end]
source=(a.source/'ap/ap_ftkd.c').read_text(encoding='latin1')
changed=runpy.run_path(str(here/'ft-kdp-event-span-composition.py'))['compose'](source)
anchor=' NdisZeroMemory(pFtKdp,sizeof(*pFtKdp));\n\tpFtKdp->Sig = EventId;'
assert changed.count(anchor)==1
function=changed[changed.index('VOID TYPE_FUNC FT_KDP_EventInform('):]
assert function.index('if (pFtKdp == NULL)')<function.index(anchor)<function.index('switch(EventId)')
body=r'''
#include <assert.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <stdio.h>
#define GNU_PACKED __attribute__((packed))
#define VOID void
#define ETH_ALEN 6
typedef uint8_t UCHAR;typedef uint16_t UINT16;
'''+declaration+r'''
#define NdisZeroMemory(p,n) memset(p,0,n)
int main(void){
 for(unsigned int EventId=0;EventId<256;EventId++){
  RT_SIGNAL_STRUC *pFtKdp=malloc(sizeof(*pFtKdp));assert(pFtKdp);
  memset(pFtKdp,0xa5,sizeof(*pFtKdp));
'''+anchor+r'''
  assert(pFtKdp->Sig==EventId);
  unsigned char *bytes=(unsigned char *)pFtKdp;
  for(size_t i=0;i<sizeof(*pFtKdp);i++)if(i!=__builtin_offsetof(RT_SIGNAL_STRUC,Sig))assert(!bytes[i]);
  free(pFtKdp);
 }
 puts("PASS | native KDP signal initialization | actual packed layout, all256 IDs, dirty allocation cleared before case-specific publication; host ABI only");return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='ft-signal-init-') as td:
 c=Path(td)/'check.c';exe=Path(td)/'check';c.write_text(body)
 subprocess.run(['cc','-std=c99','-O2','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-pie','-no-pie',str(c),'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)
