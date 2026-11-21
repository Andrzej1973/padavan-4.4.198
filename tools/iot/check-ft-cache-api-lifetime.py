#!/usr/bin/env python3
"""Execute prepared cache API leases using the existing native-type fixture."""
import argparse
import contextlib
import io
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('source',type=Path)
a=p.parse_args()
here=Path(__file__).resolve().parent
saved=sys.argv[:]
sys.argv=[str(here/'check-ft-r1kh-snapshot.py'),str(a.source)]
try:
    with contextlib.redirect_stdout(io.StringIO()):
        fixture=runpy.run_path(sys.argv[0])
finally:
    sys.argv=saved
compose=runpy.run_path(str(here/'ft-cache-api-lifetime-composition.py'))['compose_api']
source=fixture['api']['FUNCTION']
prepared=compose(source)
for bad in (prepared,source.replace('BOOLEAN wr_ft_r1kh_delete(', 'BOOLEAN changed(',1)):
    try: compose(bad)
    except ValueError: pass
    else: raise AssertionError('duplicate or missing API accepted')
prefix=fixture['prefix'].replace('typedef struct {struct {struct {int FT_R1khEntryTabLock',
    '#include "ft-cache-lifetime.h"\ntypedef struct {struct wr_ft_cache_lifetime wr_ft_cache_lifetime; int wr_ft_cache_lifetime_lock,wr_ft_cache_lifetime_initialized; struct {struct {int FT_R1khEntryTabLock',1)
assert prefix!=fixture['prefix']
prefix=prefix.replace('static void lock_cache(int *lock){assert(!*lock&&!held);*lock=held=1;}',
    'static void lock_cache(int *lock){assert(!*lock&&!held);'
    'if(observed_adapter&&lock==&observed_adapter->ApCfg.FtTab.FT_R1khEntryTabLock)'
    'assert(observed_adapter->wr_ft_cache_lifetime.owner.transactions==1);'
    '*lock=held=1;}',1)
# Trigger close after API admission, before allocation/cache access. The held
# lease must prevent native destroy even though ingress is already closed.
prefix=prefix.replace('static int fail_alloc,allocations,frees;',
 'static int fail_alloc,allocations,frees,close_on_alloc;')
prefix=prefix.replace('(void)ad;assert(!held);if(fail_alloc)return 1;', '''
 RTMP_ADAPTER *adapter=ad;
 assert(!held&&adapter->wr_ft_cache_lifetime.owner.transactions==1);
 if(close_on_alloc){
  close_on_alloc=0;
  assert(wr_ft_cache_close(&adapter->wr_ft_cache_lifetime));
  assert(!wr_ft_cache_destroy_begin(&adapter->wr_ft_cache_lifetime));
 }
 if(fail_alloc)return 1;''',1)
main=r'''
int main(void){
 RTMP_ADAPTER ad={0};FT_R1HK_ENTRY value={0},out;
 unsigned char name[16]={7};unsigned long serial;
 observed_adapter=&ad;value.PmkR1Name[0]=7;value.PmkR1Key[0]=42;
 wr_ft_cache_lifetime_init(&ad.wr_ft_cache_lifetime);
 ad.ApCfg.FtTab.FT_R1khEntryTabReady=1;
 memset(&out,0x55,sizeof(out));
 assert(!wr_ft_r1kh_snapshot(&ad,name,&out)&&!out.PmkR1Key[0]);
 assert(!wr_ft_r1kh_store(&ad,&value)&&!allocations);
 ad.wr_ft_cache_lifetime_initialized=1;
 serial=wr_ft_cache_start(&ad.wr_ft_cache_lifetime);
 assert(serial&&wr_ft_cache_publish(&ad.wr_ft_cache_lifetime,serial,1));
 assert(wr_ft_r1kh_store(&ad,&value));
 assert(wr_ft_r1kh_snapshot(&ad,name,&out)&&out.PmkR1Key[0]==42);
 assert(!ad.wr_ft_cache_lifetime.owner.transactions&&!held);
 assert(wr_ft_r1kh_delete(&ad,name));
 fail_alloc=1;
 assert(!wr_ft_r1kh_store(&ad,&value));
 assert(!ad.wr_ft_cache_lifetime.owner.transactions&&!held);
 fail_alloc=0;close_on_alloc=1;
 assert(wr_ft_r1kh_store(&ad,&value));
 assert(!ad.wr_ft_cache_lifetime.owner.transactions&&!held);
 assert(!wr_ft_r1kh_snapshot(&ad,name,&out));
 assert(!wr_ft_r1kh_delete(&ad,name));
 assert(!wr_ft_r1kh_store(&ad,&value));
 serial=wr_ft_cache_destroy_begin(&ad.wr_ft_cache_lifetime);assert(serial);
 assert(!wr_ft_cache_destroy_finish(&ad.wr_ft_cache_lifetime,serial,1));
 assert(wr_ft_cache_destroy_claim(&ad.wr_ft_cache_lifetime,serial));
 free(ad.ApCfg.FtTab.FT_R1khEntryTab[0].pHead);
 ad.ApCfg.FtTab.FT_R1khEntryTab[0].pHead=NULL;
 ad.ApCfg.FtTab.FT_R1khEntryTabReady=0;
 assert(wr_ft_cache_destroy_finish(&ad.wr_ft_cache_lifetime,serial,1));
 assert(!wr_ft_r1kh_snapshot(&ad,name,&out)&&!held);
 puts("PASS | FT cache API lifetime | cold/draining refusal, snapshot/store/delete leases, allocation failure release, close during admitted store blocks destroy");
 return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='ft-cache-api-') as td:
    c=Path(td)/'check.c';exe=Path(td)/'check'
    c.write_text(prefix+prepared+main)
    subprocess.run(['cc','-std=c99','-O2','-Wall','-Wextra','-Werror',
        '-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(c),'-o',str(exe)],check=True)
    subprocess.run([str(exe)],check=True)
