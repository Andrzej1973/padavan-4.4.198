#!/usr/bin/env python3
"""Extract whole APShutdown; radio/stop/lock lifetime operations injected."""
import argparse
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('candidate',type=Path);p.add_argument('output',type=Path)
a=p.parse_args()
if a.output.exists():p.error('new output required')
s=(a.candidate/'ap/ap.c').read_text();start=s.index('BOOLEAN APShutdown(');end=s.index('\n}',start)+2
f=s[start:end]
header=(a.candidate/'include/ap.h').read_text()
assert 'BOOLEAN APShutdown(' in header and 'VOID APShutdown(' not in header
close=(a.candidate/'common/rtmp_init_inf.c').read_text()
legacy_checked='INT RTMPDrvClose(' in close
signature=('INT' if legacy_checked else 'VOID')+' RTMPDrvClose('
if 'static INT wr_iot_legacy_close_body(' in close:
 legacy_checked=True;signature='static INT wr_iot_legacy_close_body('
start=close.index(signature);end=close.index('\n}',start)+2;legacy=close[start:end]
guard='if (!APShutdown(pAd)) return '+('NDIS_STATUS_FAILURE;' if legacy_checked else ';')
if not legacy_checked:guard='if (!APShutdown(pAd)) return;'
assert legacy.index(guard)<legacy.index('RtmpNetTaskExit(pAd)')
prefix=r'''
#include <assert.h>
#define TRUE 1
#define FALSE 0
#define RT_DEBUG_TRACE 0
#define DBGPRINT(l,a) do{(void)(l);}while(0)
typedef int BOOLEAN;
typedef struct {int MacTabLock,WdsTabLock;void *pMulticastFilterTable;} RTMP_ADAPTER;
static int radio_off,stop_calls,stop_ok,freed,igmp,wnm;
#define MlmeRadioOff(a) ((void)(a),radio_off++)
#ifdef RTMP_MAC_PCI
#define APStop(a) ((void)(a),stop_calls++,stop_ok)
#endif
#define MultiCastFilterTableReset(t) ((void)(t),igmp++)
#define DMSTable_Release(a) ((void)(a),wnm++)
#define NdisFreeSpinLock(l) ((void)(l),freed++)
'''
post=r'''
int main(void){RTMP_ADAPTER a={0};stop_ok=0;
#ifdef RTMP_MAC_PCI
assert(!APShutdown(&a)&&radio_off==1&&stop_calls==1&&!freed&&!igmp&&!wnm);
#else
assert(APShutdown(&a)&&radio_off==1&&!stop_calls);
freed=igmp=wnm=0;
#endif
stop_ok=1;assert(APShutdown(&a)&&radio_off==2);
#ifdef WDS_SUPPORT
assert(freed==2);
#else
assert(freed==1);
#endif
#ifdef IGMP_SNOOP_SUPPORT
assert(igmp==1);
#else
assert(!igmp);
#endif
#ifdef DOT11V_WNM_SUPPORT
assert(wnm==1);
#else
assert(!wnm);
#endif
return 0;}
'''
if 'NdisFreeSpinLock(&pAd->MacTabLock);' not in f:
 post=post.replace('assert(freed==2);','assert(freed==1);').replace('assert(freed==1);\n#endif','assert(freed==0);\n#endif')
 # Above replacement affects only the non-WDS branch because WDS is followed
 # by #else. Verify the adapter-owned lock is not destroyed by this routine.
 assert 'NdisFreeSpinLock(&pAd->MacTabLock);' not in f
a.output.write_text(prefix+f+post,encoding='utf-8')
print('Extracted APShutdown and actual legacy body guard order; hardware/lifetime mocked')
