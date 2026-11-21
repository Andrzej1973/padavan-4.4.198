#!/usr/bin/env python3
"""Verify generated typed guard placement against pinned event declarations."""
import argparse,runpy,re,subprocess,tempfile
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('source',type=Path);a=p.parse_args();here=Path(__file__).resolve().parent
header=(a.source/'include/ft.h').read_text()
source=(a.source/'ap/ap_ftkd.c').read_text(encoding='latin1')
changed=runpy.run_path(str(here/'ft-kdp-event-span-composition.py'))['compose'](source)
start=changed.index(' if((EventId==FT_KDP_SIG_FT_ASSOCIATION&&')
end=changed.index('return;',start)+7
guard=changed[start:end]
# Native full key element includes nested key information. Use actual struct
# block plus its immediately referenced key-info declaration.
for name in ['FT_KDP_EVT_ASSOC','FT_KDP_EVT_REASSOC','FT_KDP_EVT_KEY_ELM']:
 m=re.search(r'typedef struct GNU_PACKED [^{]+\{[^}]+\}\s*'+name+r'\s*;',header,re.S)
 if not m:raise ValueError('event declaration missing '+name)
 assert guard.count('sizeof('+name+')')==1
allocation=changed.index('FT_MEM_ALLOC(pAd, &pFtKdp, sizeof(FT_KDP_SIGNAL));',start)
assert end<allocation
for read in ('pEvtAssoc = (FT_KDP_EVT_ASSOC *)pEvent;',
             'pEvtReAssoc = (FT_KDP_EVT_REASSOC *)pEvent;',
             'pEvtKeyReq = (FT_KDP_EVT_KEY_ELM *)pEvent;'):
 assert changed.index(read,start)>end
try:runpy.run_path(str(here/'ft-kdp-event-span-composition.py'))['compose'](changed)
except ValueError:pass
else:raise AssertionError('duplicate accepted')
print('PASS typed event guard source placement: three vendor sizeof bounds before allocation/typed reads; full native producer and target compilation pending')
# Execute the generated preflight with actual packed declarations. This tests
# admission semantics, not the rest of EventInform or target ABI compilation.
constants=(a.source/'include/ft_cmm.h').read_text()
declarations=[]
for name in ('FT_KDP_PMK_KEY_INFO','FT_KDP_EVT_ASSOC','FT_KDP_EVT_REASSOC','FT_KDP_EVT_KEY_ELM'):
 m=re.search(r'typedef struct GNU_PACKED [^{]+\{[^}]+\}\s*'+name+r'\s*;',header,re.S)
 if not m:raise ValueError('missing native type '+name)
 declarations.append(m[0])
needed=set(re.findall(r'FT_KDP_\w+_MAX_SIZE','\n'.join(declarations)))
defines=[]
for name in sorted(needed):
 m=re.search(r'^#define\s+'+name+r'\s+([^\n]+)',constants,re.M)
 if not m:raise ValueError('missing native constant '+name)
 defines.append(m[0])
program=r'''
#include <assert.h>
#include <stdlib.h>
#include <stdio.h>
#include <stdint.h>
#define GNU_PACKED __attribute__((packed))
#define ETH_ALEN 6
typedef uint8_t UCHAR;typedef uint16_t UINT16;typedef uint32_t UINT32;
#define FT_KDP_SIG_FT_ASSOCIATION 1
#define FT_KDP_SIG_FT_REASSOCIATION 2
#define FT_KDP_SIG_KEY_REQ 3
'''+ '\n'.join(defines+declarations)+r'''
static void preflight(unsigned int EventId,unsigned int EventLen,
 unsigned int PeerIP,const void *pEvent,int *accepted){
'''+guard+r'''
 *accepted=1;
}
int main(void){
 size_t sizes[]={sizeof(FT_KDP_EVT_ASSOC),sizeof(FT_KDP_EVT_REASSOC),sizeof(FT_KDP_EVT_KEY_ELM)};
 for(unsigned id=1;id<=3;id++)for(unsigned peer=0;peer<=1;peer++)for(unsigned n=0;n<=1024;n++){
  void *input=malloc(n?n:1);assert(input);int accepted=0;
  preflight(id,n,peer,input,&accepted);
  assert(accepted==(int)((id==3&&peer)||n>=sizes[id-1]));
  accepted=0;preflight(id,n,peer,NULL,&accepted);
  assert(accepted==(int)(id==3&&peer));free(input);
 }
 printf("PASS typed event guard execution: vendor sizes %zu/%zu/%zu; lengths0-1024, NULL and PeerIP branches; host ABI only\n",sizes[0],sizes[1],sizes[2]);return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='ft-event-types-') as td:
 c=Path(td)/'check.c';exe=Path(td)/'check';c.write_text(program)
 subprocess.run(['cc','-std=c99','-O2','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-pie','-no-pie',str(c),'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)
