#!/usr/bin/env python3
"""Execute prepared native EventGet with pinned queue/list implementations."""
import argparse,contextlib,io,runpy,subprocess,sys,tempfile
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('source',type=Path);a=p.parse_args();here=Path(__file__).resolve().parent
saved=sys.argv[:];sys.argv=[str(here/'check-ft-kdp-event-output.py'),str(a.source)]
try:
 with contextlib.redirect_stdout(io.StringIO()):fixture=runpy.run_path(sys.argv[0])
finally:sys.argv=saved
header=(a.source/'include/ft.h').read_text()
macros=header[header.index('#define FT_KDP_EVT_LIST_REMOVE_HEAD'):header.index('#define FT_KDP_EVT_LIST_EMPTY')]
admit=runpy.run_path(str(here/'ft-kdp-event-output-composition.py'))['compose_admission']
body=r'''
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "ft-cache-lifetime.h"
#define VOID void
#define TYPE_FUNC
#define IN
#define OUT
#define DBGPRINT(level,args) ((void)0)
typedef unsigned char UCHAR;
'''+(a.source/'include/link_list.h').read_text()+r'''
typedef struct {RT_LIST_ENTRY link;unsigned int marker;} FT_KDP_SIGNAL;
typedef struct {LIST_HEADER EventList;} BLOCK;
typedef struct {struct {struct {int FlgIsFtKdpInit,FT_KdpLock;BLOCK *pFT_KDP_Ctrl_BK;}FtTab;}ApCfg;struct wr_ft_cache_lifetime wr_ft_cache_lifetime;int wr_ft_cache_lifetime_initialized,wr_ft_cache_lifetime_lock;} AD;
#define PRTMP_ADAPTER AD *
#define FT_KDP_CB (pAd->ApCfg.FtTab.pFT_KDP_Ctrl_BK)
static int held,locks,drain_after_size,close_after_size;
static AD *observed;
static void lock(int *p){if(observed&&p==&observed->ApCfg.FtTab.FT_KdpLock)assert(observed->wr_ft_cache_lifetime.owner.transactions==1);assert(!*p&&!held);*p=held=1;locks++;}
static void unlock(int *p){assert(*p&&held);*p=held=0;
 if(observed&&p==&observed->ApCfg.FtTab.FT_KdpLock&&close_after_size){close_after_size=0;assert(wr_ft_cache_close(&observed->wr_ft_cache_lifetime));assert(!wr_ft_cache_destroy_begin(&observed->wr_ft_cache_lifetime));}
 if(observed&&p==&observed->ApCfg.FtTab.FT_KdpLock&&drain_after_size){drain_after_size=0;removeHeadList(&observed->ApCfg.FtTab.pFT_KDP_Ctrl_BK->EventList);}}
#define RTMP_SEM_LOCK(p) lock(p)
#define RTMP_SEM_UNLOCK(p) unlock(p)
'''+macros+admit(fixture['native'])+r'''
int main(void){
 AD ad={0};BLOCK block={0};FT_KDP_SIGNAL node={.marker=42},*out;
 observed=&ad;ad.ApCfg.FtTab.pFT_KDP_Ctrl_BK=&block;
 wr_ft_cache_lifetime_init(&ad.wr_ft_cache_lifetime);
 out=&node;FT_KDP_EventGet(&ad,&out);assert(!out&&!locks);
 ad.wr_ft_cache_lifetime_initialized=1;
 out=&node;FT_KDP_EventGet(&ad,&out);assert(!out&&!held);
 unsigned long serial=wr_ft_cache_start(&ad.wr_ft_cache_lifetime);
 assert(serial&&wr_ft_cache_publish(&ad.wr_ft_cache_lifetime,serial,1));
 locks=0;
 initList(&block.EventList);
 out=&node;FT_KDP_EventGet(&ad,&out);assert(!out&&!held&&!ad.wr_ft_cache_lifetime.owner.transactions);locks=0;
 ad.ApCfg.FtTab.FlgIsFtKdpInit=1;
 out=&node;FT_KDP_EventGet(&ad,&out);assert(!out&&!held);
 insertTailList(&block.EventList,&node.link);
 FT_KDP_EventGet(&ad,&out);
#if !defined(FT_KDP_EMPTY) && !defined(FT_KDP_FUNC_SOCK_COMM)
 assert(out==&node&&out->marker==42&&!getListSize(&block.EventList));
 insertTailList(&block.EventList,&node.link);
 drain_after_size=1;out=&node;
 FT_KDP_EventGet(&ad,&out);assert(!out&&!getListSize(&block.EventList));
 insertTailList(&block.EventList,&node.link);close_after_size=1;
 FT_KDP_EventGet(&ad,&out);assert(out==&node&&!ad.wr_ft_cache_lifetime.owner.transactions);
#else
 assert(!out&&getListSize(&block.EventList)==1);
#endif
 FT_KDP_EventGet(&ad,NULL);assert(!held);
 assert(wr_ft_cache_close(&ad.wr_ft_cache_lifetime));
 int prior=locks;out=&node;FT_KDP_EventGet(&ad,&out);
 assert(!out&&locks==prior+1&&!ad.wr_ft_cache_lifetime.owner.transactions);
 assert(wr_ft_cache_destroy_begin(&ad.wr_ft_cache_lifetime));
 puts("PASS | FT native EventGet | lifetime lease plus actual queue macros/list helpers; init/empty/null output, detached identity and competing dequeue; socket/empty branches leave queue untouched");return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='ft-event-native-') as td:
 c=Path(td)/'check.c';c.write_text(body)
 for i,flags in enumerate(([],['-DFT_KDP_FUNC_SOCK_COMM'],['-DFT_KDP_EMPTY'])):
  exe=Path(td)/str(i)
  subprocess.run(['cc','-std=c99','-O2','-Wall','-Wextra','-Werror','-Wno-unused-function','-Wno-unused-parameter','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),*flags,str(c),'-o',str(exe)],check=True)
  subprocess.run([str(exe)],check=True)
