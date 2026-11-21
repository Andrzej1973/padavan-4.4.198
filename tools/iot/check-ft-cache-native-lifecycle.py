#!/usr/bin/env python3
"""Execute checked entry points with pinned native cache init/destroy bodies."""
import argparse,contextlib,io,runpy,subprocess,sys,tempfile
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);a=p.parse_args()
here=Path(__file__).resolve().parent
saved=sys.argv[:];sys.argv=[str(here/'check-ft-cache-api-lifetime.py'),str(a.source)]
try:
 with contextlib.redirect_stdout(io.StringIO()):fixture=runpy.run_path(sys.argv[0])
finally:sys.argv=saved
compose=runpy.run_path(str(here/'ft-cache-native-lifecycle-composition.py'))['compose']
source=(a.source/'common/ft.c').read_text()
native=compose(source)
for bad in (native,source.replace('VOID FT_R1khEntryTabInit(','VOID changed(',1)):
 try:compose(bad)
 except ValueError:pass
 else:raise AssertionError('missing/duplicate native lifecycle accepted')
prefix=fixture['prefix'].replace('assert(!held);free(p);frees++;',
 'assert(observed_adapter->wr_ft_cache_lifetime.phase==WR_FT_CACHE_FREEING||!held);free(p);frees++;',1)
prefix=prefix.replace('assert(observed_adapter->wr_ft_cache_lifetime.owner.transactions==1);',
 'assert(observed_adapter->wr_ft_cache_lifetime.owner.transactions==1||observed_adapter->wr_ft_cache_lifetime.phase==WR_FT_CACHE_FREEING);')
stubs=r'''
#define VOID void
typedef UCHAR *PUCHAR;
#define IN
#define PRTMP_ADAPTER RTMP_ADAPTER *
typedef __typeof__(((RTMP_ADAPTER *)0)->ApCfg.FtTab) *PFT_TAB;
#define FT_R1KH_ENTRY_HASH_TABLE_SIZE 1
static int lock_allocs,lock_frees,fail_lock,duplicate_attempts;
BOOLEAN wr_ft_cache_release_reserved(RTMP_ADAPTER *,unsigned long);
static int allocate_lock(RTMP_ADAPTER *ad,int *lock){
 assert(!held&&ad->wr_ft_cache_lifetime.phase==WR_FT_CACHE_STARTING);
 lock_allocs++;if(fail_lock)return 0;*lock=0;return 1;
}
#define NdisAllocateSpinLock(ad,lock) allocate_lock(ad,lock)
static void free_lock(int *lock){
 assert(!held&&!*lock);
 assert(observed_adapter->wr_ft_cache_lifetime.phase==WR_FT_CACHE_FREEING);
 assert(!wr_ft_cache_release_reserved(observed_adapter,
  observed_adapter->wr_ft_cache_lifetime.owner.serial));
 duplicate_attempts++;lock_frees++;
}
#define NdisFreeSpinLock(lock) free_lock(lock)
'''
main=r'''
int main(void){
 RTMP_ADAPTER ad={0};FT_R1HK_ENTRY value={0},out;
 struct wr_ft_cache_lease lease={0};unsigned char name[16]={7};unsigned long serial;
 observed_adapter=&ad;wr_ft_cache_lifetime_init(&ad.wr_ft_cache_lifetime);
 assert(!wr_ft_cache_initialize_checked(&ad)&&!lock_allocs);
 ad.wr_ft_cache_lifetime_initialized=1;
 assert(wr_ft_cache_initialize_checked(&ad)&&lock_allocs==1);
 assert(!wr_ft_cache_initialize_checked(&ad)&&lock_allocs==1);
 assert(ad.ApCfg.FtTab.FT_R1khEntryTabReady&&!held);
 value.PmkR1Name[0]=7;assert(wr_ft_r1kh_store(&ad,&value));
 assert(wr_ft_cache_enter(&ad.wr_ft_cache_lifetime,&lease));
 assert(!wr_ft_cache_release_checked(&ad)&&!lock_frees);
 assert(ad.ApCfg.FtTab.FT_R1khEntryTabReady);
 assert(!wr_ft_r1kh_snapshot(&ad,name,&out));
 assert(wr_ft_cache_leave(&ad.wr_ft_cache_lifetime,&lease));
 serial=wr_ft_cache_release_reserve(&ad);assert(serial&&!lock_frees);
 assert(!wr_ft_cache_release_reserve(&ad));
 assert(!wr_ft_cache_initialize_checked(&ad));
 assert(!wr_ft_cache_release_reserved(&ad,serial+1)&&!lock_frees);
 assert(wr_ft_cache_release_reserved(&ad,serial)&&lock_frees==1&&frees==1);
 assert(!wr_ft_cache_release_reserved(&ad,serial)&&lock_frees==1);
 assert(!ad.ApCfg.FtTab.FT_R1khEntryTabReady&&!held);
 assert(!wr_ft_cache_release_checked(&ad)&&lock_frees==1);
 assert(wr_ft_cache_initialize_checked(&ad)&&lock_allocs==2);
 assert(!ad.ApCfg.FtTab.FT_R1khEntryTabSize);
 assert(wr_ft_cache_release_checked(&ad)&&lock_frees==2&&duplicate_attempts==2);
#ifdef OS_ABL_FUNC_SUPPORT
 fail_lock=1;
 assert(!wr_ft_cache_initialize_checked(&ad));
 assert(!ad.ApCfg.FtTab.FT_R1khEntryTabReady);
 assert(ad.wr_ft_cache_lifetime.owner.poisoned&&ad.wr_ft_cache_lifetime.owner.active);
 assert(!wr_ft_cache_initialize_checked(&ad)&&!wr_ft_cache_release_checked(&ad));
 assert(!wr_ft_r1kh_snapshot(&ad,name,&out)&&!held);
#endif
 puts("PASS | FT checked native cache lifecycle | init outside lifetime lock, close/drain before native destroy, retry after holder return, reopen, allocation failure retention");
 return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='ft-native-cache-') as td:
 c=Path(td)/'check.c';c.write_text(prefix+stubs+fixture['prepared']+native+main)
 for flags in ([],['-DOS_ABL_FUNC_SUPPORT']):
  exe=Path(td)/('abl' if flags else 'direct')
  subprocess.run(['cc','-std=gnu99','-O2','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),*flags,str(c),'-o',str(exe)],check=True)
  subprocess.run([str(exe)],check=True)
