#!/usr/bin/env python3
"""Check native source preservation and outer-return balancing; no SDK body execution."""
import argparse,runpy,subprocess,tempfile
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);a=p.parse_args()
here=Path(__file__).resolve().parent;module=runpy.run_path(str(here/'ra2-mutation-wrappers.py'))
for name,sites in module['SITES'].items():
    original=(a.source/name).read_text();changed,receipts=module['compose'](name,original)
    restored=changed
    for wrapper,old in reversed(receipts):
        assert restored.count(wrapper)==1
        restored=restored.replace(wrapper,old,1)
    assert restored==original
    try:module['compose'](name,changed)
    except ValueError:pass
    else:raise AssertionError('duplicate wrapping accepted')
    # Execute the exact generated wrappers with an SDK boundary actor replacing
    # the untouched native body. The actor returns immediately, as any native
    # early return would. This tests wrapping and release, not station behavior.
    for (function,static,reassoc),(wrapper,_) in zip(sites,receipts):
        declarations=wrapper[:wrapper.rindex('static VOID wr_ra2_native_')]
        raw='wr_ra2_native_'+function
        args='RTMP_ADAPTER *pAd,MLME_QUEUE_ELEM *Elem'+(',BOOLEAN isReassoc' if reassoc else '')
        unit='''#include <assert.h>
#include "ra2-association-owner.h"
#define VOID void
typedef int BOOLEAN;
typedef struct {int mode,enters,leaves,bodies;struct wr_ra2_assoc_owner owner;} RTMP_ADAPTER;
typedef struct {int unused;} MLME_QUEUE_ELEM;
static int wr_ra2_mutation_enter(RTMP_ADAPTER *ad,MLME_QUEUE_ELEM *e,struct wr_ra2_assoc_ticket *t){
 (void)e;ad->enters++;if(ad->mode<=0)return ad->mode;
 return wr_ra2_assoc_enter(&ad->owner,t,0)?1:-1;
}
static void wr_ra2_mutation_leave(RTMP_ADAPTER *ad,struct wr_ra2_assoc_ticket *t){
 ad->leaves++;assert(wr_ra2_assoc_leave(&ad->owner,t));
}
'''+declarations+'static VOID '+raw+'('+args+'){(void)Elem;'+('(void)isReassoc;' if reassoc else '')+'pAd->bodies++;return;}\n'
        call=function+'(&ad,&event'+(',1' if reassoc else '')+');'
        unit+='int main(void){for(int mode=-1;mode<=1;mode++){RTMP_ADAPTER ad={.mode=mode};MLME_QUEUE_ELEM event={0};'+call+'''
#if defined(MT7603) && defined(MT_MAC) && defined(RTMP_PCI_SUPPORT)
 assert(ad.enters==1&&ad.bodies==(mode>=0)&&ad.leaves==(mode>0));
#else
 assert(!ad.enters&&ad.bodies==1&&!ad.leaves);
#endif
 assert(!ad.owner.associations); }return 0;}'''
        with tempfile.TemporaryDirectory(prefix='wr-ra2-mutation-wrap-') as temp:
            d=Path(temp);(d/'test.c').write_text(unit)
            for flags in ([],['-DMT7603','-DMT_MAC','-DRTMP_PCI_SUPPORT']):
                subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-Wno-unused-function','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie',*flags,'-I'+str(here),str(d/'test.c'),'-o',str(d/'test')],check=True)
                subprocess.run([str(d/'test')],check=True)
print('Three native outer wrappers preserved and boundary returns balanced; Linux admission unbound')
