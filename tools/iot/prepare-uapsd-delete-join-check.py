#!/usr/bin/env python3
"""Extract deletion admission only; injected locks are not a lifetime proof."""
import argparse
from pathlib import Path

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('candidate', type=Path)
p.add_argument('output', type=Path)
a = p.parse_args()
if a.output.exists():
    p.error('new output required')
s = (a.candidate / 'mgmt/mgmt_entrytb.c').read_text()
begin = '/* Deletion-only join; caller owns MacTabLock and verified address. */'
end = '/* End deletion-only queue join. */'
if s.count(begin) != 1 or s.count(end) != 1:
    p.error('unique admission boundaries required')
body = s[s.index(begin):s.index(end)]
if s.index(begin) >= s.index('tr_tb_reset_entry(pAd, wcid);'):
    p.error('join must precede TR destruction')
prefix = r'''
#include <assert.h>
#define FALSE 0
#define NDIS_STATUS_SUCCESS 0
#define WRITE_ONCE(x,v) do { assert(irq && mac); (x)=(v); } while(0)
typedef unsigned long ULONG;
struct tr { int enq_cap,deq_cap; };
typedef struct { int irq_lock,MacTabLock; struct tr tr; } RTMP_ADAPTER;
static int irq,mac,result,joined,destructive;
#define RTMP_IRQ_LOCK(l,f) do { (void)(l); (f)=0; assert(mac&&!irq); irq=1; } while(0)
#define RTMP_IRQ_UNLOCK(l,f) do { (void)(l); (void)(f); assert(irq); irq=0; } while(0)
#define NdisReleaseSpinLock(l) do { (void)(l); assert(mac&&!irq); mac=0; } while(0)
#ifdef UAPSD_SUPPORT
static int wr_iot_uapsd_retire_queues(RTMP_ADAPTER *a,void *e) {
 (void)e; assert(mac&&!irq&&!a->tr.enq_cap&&!a->tr.deq_cap);
 joined++; return result;
}
#endif
static int admission(RTMP_ADAPTER *pAd) {
 struct tr *tr_entry=&pAd->tr;
#ifdef UAPSD_SUPPORT
 void *pEntry=0;
#endif
'''
suffix = r'''
 assert(mac&&!irq); destructive++;
 NdisReleaseSpinLock(&pAd->MacTabLock); return 1;
}
int main(void) {
 RTMP_ADAPTER a={0};
#ifdef UAPSD_SUPPORT
 result=-1; mac=1; a.tr.enq_cap=a.tr.deq_cap=1;
 assert(admission(&a)==0); assert(!mac&&!irq&&!destructive&&joined==1);
 assert(!a.tr.enq_cap&&!a.tr.deq_cap);
#endif
 result=0; mac=1; a.tr.enq_cap=a.tr.deq_cap=1;
 assert(admission(&a)==1); assert(!mac&&!irq&&destructive==1);
#ifdef UAPSD_SUPPORT
 assert(joined==2);
#else
 assert(!joined);
#endif
 return 0;
}
'''
a.output.write_text(prefix + body + suffix, encoding='utf-8')
print('Extracted admission only: real prior side effects/callback lifetime/recovery unproved')
