#!/usr/bin/env python3
"""Check uninstalled FT outer wrapper source and balanced boundary execution."""
import argparse,runpy,subprocess,tempfile
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);a=p.parse_args()
here=Path(__file__).resolve().parent
native=(a.source/'common/ft.c').read_text()
compose=runpy.run_path(str(here/'ra2-ft-mutation-composition.py'))['compose']
changed,receipts=compose(native);assert len(receipts)==1
wrapper,old=receipts[0];assert changed.replace(wrapper,old,1)==native
try:compose(changed)
except ValueError:pass
else:raise AssertionError('duplicate FT wrapper accepted')
# Real native body is preserved, but replaced by an early-return actor here.
declarations=wrapper[:wrapper.rindex('static VOID wr_ra2_native_')]
code='''#include <assert.h>
#define VOID void
#include "ra2-association-owner.h"
typedef struct {int mode,enters,leaves,bodies;struct wr_ra2_assoc_owner owner;} RTMP_ADAPTER;
typedef struct {int unused;} MLME_QUEUE_ELEM;
static int wr_ra2_mutation_enter(RTMP_ADAPTER *ad,MLME_QUEUE_ELEM *e,struct wr_ra2_assoc_ticket *t){
 (void)e;ad->enters++;if(ad->mode<=0)return ad->mode;
 return wr_ra2_assoc_enter(&ad->owner,t,0)?1:-1;
}
static void wr_ra2_mutation_leave(RTMP_ADAPTER *ad,struct wr_ra2_assoc_ticket *t){
 ad->leaves++;assert(wr_ra2_assoc_leave(&ad->owner,t));
}
'''+declarations+'''
static VOID wr_ra2_native_FT_FtAction(RTMP_ADAPTER *ad,MLME_QUEUE_ELEM *e){(void)e;ad->bodies++;return;}
int main(void){for(int mode=-1;mode<=1;mode++){
 RTMP_ADAPTER ad={.mode=mode};MLME_QUEUE_ELEM event={0};FT_FtAction(&ad,&event);
#if defined(MT7603) && defined(MT_MAC) && defined(RTMP_PCI_SUPPORT)
 assert(ad.enters==1&&ad.bodies==(mode>=0)&&ad.leaves==(mode>0));
#else
 assert(!ad.enters&&ad.bodies==1&&!ad.leaves);
#endif
 assert(!ad.owner.associations);
 }return 0;}
'''
with tempfile.TemporaryDirectory(prefix='wr-ft-wrap-') as td:
 src=Path(td)/'check.c';exe=Path(td)/'check';src.write_text(code)
 for flags in ([],['-DMT7603','-DMT_MAC','-DRTMP_PCI_SUPPORT']):
  subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-Wno-unused-function','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie',*flags,'-I'+str(here),str(src),'-o',str(exe)],check=True)
  subprocess.run([str(exe)],check=True)
print('Prepared FT wrapper: native bytes preserved, refusal/pass-through/early-return release PASS; BSS/provenance/native body and target unverified')
