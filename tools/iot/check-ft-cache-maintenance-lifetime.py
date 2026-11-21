#!/usr/bin/env python3
"""Execute pinned native maintenance behind prepared lifetime admission."""
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
a=p.parse_args();here=Path(__file__).resolve().parent
saved=sys.argv[:];sys.argv=[str(here/'check-ft-cache-api-lifetime.py'),str(a.source)]
try:
    with contextlib.redirect_stdout(io.StringIO()):
        fixture=runpy.run_path(sys.argv[0])
finally:
    sys.argv=saved
api=runpy.run_path(str(here/'ft-cache-api-lifetime-composition.py'))
source=(a.source/'common/ft.c').read_text()
start=source.index('VOID FT_R1KHInfoMaintenance(')
native=source[start:source.index('\n}',start)+2]
prepared=api['compose_maintenance'](fixture['prepared']+'\n'+native)
assert native.replace('VOID FT_R1KHInfoMaintenance(',
    'static VOID wr_ft_r1kh_maintenance_native(',1) in prepared
for bad in (prepared,native,fixture['prepared']+'\n'+native+native):
    try:api['compose_maintenance'](bad)
    except ValueError:pass
    else:raise AssertionError('missing predecessor or duplicate accepted')
prefix=fixture['prefix'].replace('assert(!held);free(p);frees++;',
    'assert(observed_adapter->wr_ft_cache_lifetime.owner.transactions==1);free(p);frees++;',1)
stubs=r'''
#define VOID void
#define IN
#define PRTMP_ADAPTER RTMP_ADAPTER *
typedef __typeof__(((RTMP_ADAPTER *)0)->ApCfg.FtTab) *PFT_TAB;
#define FT_R1KH_ENTRY_HASH_TABLE_SIZE 1
typedef struct {unsigned int wcid;} MAC_TABLE_ENTRY,*PMAC_TABLE_ENTRY;
typedef struct {int unused;} MLME_DISASSOC_REQ_STRUCT;
#define DBGPRINT(level,args) ((void)0)
#define MLME_UNSPECIFY_FAIL 0
#define AP_ASSOC_STATE_MACHINE 1
#define APMT2_MLME_DISASSOC_REQ 2
#define FT_KDP_SIG_KEY_TIMEOUT 3
#define PVOID void *
static int lookups,enqueues,events,close_during_lookup;
static MAC_TABLE_ENTRY client={7};
static PMAC_TABLE_ENTRY MacTableLookup(RTMP_ADAPTER *ad,const unsigned char *mac){
 (void)mac;assert(held&&ad->wr_ft_cache_lifetime.owner.transactions==1);
 lookups++;
 if(close_during_lookup){
  close_during_lookup=0;
  /* Deterministic interleaving with another lifetime-lock holder. Native
   * maintenance still owns the cache lock and the lease during this event. */
  assert(wr_ft_cache_close(&ad->wr_ft_cache_lifetime));
  assert(!wr_ft_cache_destroy_begin(&ad->wr_ft_cache_lifetime));
 }
 return &client;
}
static void DisassocParmFill(RTMP_ADAPTER *ad,MLME_DISASSOC_REQ_STRUCT *req,
 const unsigned char *mac,int reason){(void)ad;(void)req;(void)mac;(void)reason;}
static void MlmeEnqueue(RTMP_ADAPTER *ad,int machine,int msg,size_t size,void *data,int extra){
 (void)ad;(void)machine;(void)msg;(void)size;(void)data;(void)extra;enqueues++;
}
static void inform(RTMP_ADAPTER *ad,int bss,int signal,const unsigned char *mac,int len,void *extra){
 (void)ad;(void)bss;(void)signal;(void)mac;(void)len;(void)extra;events++;
}
#define FT_KDP_EVENT_INFORM inform
'''
main=r'''
int main(void){
 RTMP_ADAPTER ad={0};unsigned long serial;FT_R1HK_ENTRY *entry;
 observed_adapter=&ad;wr_ft_cache_lifetime_init(&ad.wr_ft_cache_lifetime);
 FT_R1KHInfoMaintenance(&ad);assert(!held&&!lookups);
 ad.wr_ft_cache_lifetime_initialized=1;
 serial=wr_ft_cache_start(&ad.wr_ft_cache_lifetime);
 assert(serial&&wr_ft_cache_publish(&ad.wr_ft_cache_lifetime,serial,1));
 FT_R1KHInfoMaintenance(&ad); /* native Ready early return must release */
 assert(!held&&!ad.wr_ft_cache_lifetime.owner.transactions);
 ad.ApCfg.FtTab.FT_R1khEntryTabReady=1;
 entry=calloc(1,sizeof(*entry));assert(entry);entry->KeyLifeTime=1;
 initList(&ad.ApCfg.FtTab.FT_R1khEntryTab[0]);
 insertTailList(&ad.ApCfg.FtTab.FT_R1khEntryTab[0],(RT_LIST_ENTRY *)entry);
 ad.ApCfg.FtTab.FT_R1khEntryTabSize=1;
 FT_R1KHInfoMaintenance(&ad);
 assert(!entry->KeyLifeTime&&!lookups&&!held);
 close_during_lookup=1;FT_R1KHInfoMaintenance(&ad);
 assert(lookups==1&&enqueues==1&&events==1&&frees==1);
 assert(!held&&!ad.wr_ft_cache_lifetime.owner.transactions);
 assert(!ad.ApCfg.FtTab.FT_R1khEntryTabSize);
 FT_R1KHInfoMaintenance(&ad);assert(lookups==1);
 serial=wr_ft_cache_destroy_begin(&ad.wr_ft_cache_lifetime);assert(serial);
 assert(!wr_ft_cache_destroy_finish(&ad.wr_ft_cache_lifetime,serial,1));
 assert(wr_ft_cache_destroy_claim(&ad.wr_ft_cache_lifetime,serial));
 assert(wr_ft_cache_destroy_finish(&ad.wr_ft_cache_lifetime,serial,1));
 FT_R1KHInfoMaintenance(&ad);assert(!held&&lookups==1);
 puts("PASS | FT native maintenance lifetime | preserved native body, Ready early return, live expiry, close during callback blocks destroy, late ingress refusal");
 return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='ft-maintenance-') as td:
    c=Path(td)/'check.c';exe=Path(td)/'check'
    c.write_text(prefix+stubs+prepared+main)
    subprocess.run(['cc','-std=gnu99','-O2','-Wall','-Wextra','-Werror',
      '-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(c),'-o',str(exe)],check=True)
    subprocess.run([str(exe)],check=True)
