#!/usr/bin/env python3
"""Verify fresh-adapter placement and execute both lock-allocation branches."""
import argparse
from pathlib import Path
import runpy
import subprocess
import tempfile
p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);a=p.parse_args()
here=Path(__file__).resolve().parent
api=runpy.run_path(str(here/'ft-cache-storage-composition.py'))
source=(a.source/'common/rtmp_init.c').read_text(encoding='latin1')
anchor='\t\t\tpAd->OS_Cookie = handle;'
assert source.count(anchor)==1
# Supply the documented pending/request-storage predecessor at its pinned site.
predecessor=source.replace(anchor,'#ifdef DOT11R_FT_SUPPORT\n wr_ft_pending_ledger_init(&pAd->wr_ft_pending);\n#endif\n'+anchor,1)
base={'include/rtmp.h':'#ifdef DOT11R_FT_SUPPORT\n#include "ft-iapp-request-state.h"\n#endif\nstruct X {\n#ifdef DOT11R_FT_SUPPORT\n struct wr_ft_iapp_request_state wr_ft_iapp_requests;\n#endif\n};',
 'common/rtmp_init.c':predecessor}
prepared=api['compose'](base,here)
assert prepared['common/rtmp_init.c'].count(api['INITIALIZE'])==1
for invalid in (prepared,{},dict(base,**{'common/rtmp_init.c':predecessor.replace('initList(&pAd->RscLockMemList);','',1)})):
    try:api['compose'](invalid,here)
    except ValueError:pass
    else:raise AssertionError('storage drift or duplicate accepted')
program=r'''
#include <assert.h>
#include <stdio.h>
#include "ft-cache-lifetime.h"
#include "ft-ap-stop-owner.h"
#define TRUE 1
#define FALSE 0
typedef struct {struct wr_ft_ap_stop_owner wr_ft_ap_stop_owner;struct wr_ft_cache_lifetime wr_ft_cache_lifetime;
 int wr_ft_cache_lifetime_initialized,wr_ft_cache_lifetime_lock;} AD;
static int fail_alloc,allocations;
#ifdef OS_ABL_FUNC_SUPPORT
static int allocate(AD *ad,int *lock){(void)ad;allocations++;if(fail_alloc)return 0;*lock=1;return 1;}
#define NdisAllocateSpinLock(ad,lock) allocate(ad,lock)
#else
#define NdisAllocateSpinLock(ad,lock) do{(void)(ad);allocations++;*(lock)=1;}while(0)
#endif
static void initialize(AD *pAd){
'''+api['INITIALIZE']+r'''
}
int main(void){
 for(fail_alloc=0;fail_alloc<=1;fail_alloc++){
  AD ad={0};int before=allocations;
  initialize(&ad);assert(allocations==before+1);
  assert(ad.wr_ft_cache_lifetime.phase==WR_FT_CACHE_COLD);
  assert(!ad.wr_ft_ap_stop_owner.active&&!ad.wr_ft_ap_stop_owner.running&&!ad.wr_ft_ap_stop_owner.cache_ticket);
  assert(ad.wr_ft_cache_lifetime.owner.closed);
#ifdef OS_ABL_FUNC_SUPPORT
  if(fail_alloc){
   assert(!ad.wr_ft_cache_lifetime_initialized);
   assert(!ad.wr_ft_cache_lifetime_lock&&ad.wr_ft_cache_lifetime.owner.poisoned);
   assert(!wr_ft_cache_start(&ad.wr_ft_cache_lifetime));continue;
  }
#endif
  assert(ad.wr_ft_cache_lifetime_initialized&&ad.wr_ft_cache_lifetime_lock);
  assert(!ad.wr_ft_cache_lifetime.owner.poisoned);
 }
 return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='ft-cache-storage-') as td:
    c=Path(td)/'check.c';c.write_text(program)
    for flags in ([],['-DOS_ABL_FUNC_SUPPORT']):
        exe=Path(td)/('check-abl' if flags else 'check-direct')
        subprocess.run(['cc','-std=c99','-O2','-Wall','-Wextra','-Werror',
          '-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),*flags,str(c),'-o',str(exe)],check=True)
        subprocess.run([str(exe)],check=True)
print('PASS | FT cache storage | fresh allocation after resource-list init, direct/OS_ABL branches, allocation failure retains closed poisoned state, duplicate/drift refusal')
