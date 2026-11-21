#!/usr/bin/env python3
"""Extract EOSP failure tails and check release followed by later cleanup."""
import argparse
from pathlib import Path

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('candidate', type=Path)
p.add_argument('output', type=Path)
a = p.parse_args()
if a.output.exists():
    p.error('new output required')
s = (a.candidate / 'common/uapsd.c').read_text()
marker = '/* Clear shared ownership before releasing rejected EOSP. */'
if s.count(marker) != 3:
    p.error('three repaired failure tails required')
prefix = r'''
#include <assert.h>
#include <stddef.h>
typedef struct {int freed;} PACKET;
typedef struct {PACKET *pUAPSDEOSPFrame;int bAPSDFlagEOSPOK,bAPSDFlagLegacySent,bAPSDFlagSPStart;} ENTRY;
typedef struct {int UAPSDEOSPLock,bAPSDFlagSPSuspend;} ADAPTER;
static int held,releases;
#define NDIS_STATUS_FAILURE -1
#define RELEASE_NDIS_PACKET(a,p,s) do{(void)(a);(void)(s);assert(held);assert((p)!=NULL);assert(!(p)->freed);assert(pEntry->pUAPSDEOSPFrame==NULL);(p)->freed=1;releases++;}while(0)
#define UAPSD_SP_END(a,e) do{(void)(a);(void)(e);assert(held);}while(0)
#define UAPSD_SEM_UNLOCK(l,f) do{(void)(l);(void)(f);assert(held);held=0;}while(0)
'''
functions = []
for i, chunk in enumerate(s.split(marker)[1:]):
    tail = chunk[:chunk.index('return;') + len('return;')]
    functions.append('static void rejected_%d(ADAPTER *pAd,ENTRY *pEntry,PACKET *pPkt){\n'
                     'unsigned long flags=0,flags2=0;(void)flags;(void)flags2;\n' % i
                     + tail + '\n}\n')
suffix = r'''
int main(void){
 ADAPTER a={0};PACKET packets[3]={{0},{0},{0}};ENTRY e={0};
 void (*callbacks[3])(ADAPTER*,ENTRY*,PACKET*)={rejected_0,rejected_1,rejected_2};
 for(int i=0;i<3;i++){
  e=(ENTRY){&packets[i],1,1,1};held=1;
  callbacks[i](&a,&e,&packets[i]);
  assert(!held&&!e.pUAPSDEOSPFrame&&!e.bAPSDFlagEOSPOK);
  if(i<2)assert(!e.bAPSDFlagLegacySent);
  /* A subsequent retirement sees no shared EOSP ownership. */
  assert(e.pUAPSDEOSPFrame==NULL&&packets[i].freed&&releases==i+1);
 }
 return 0;
}
'''
a.output.write_text(prefix + ''.join(functions) + suffix, encoding='utf-8')
print('Extracted three rejection tails; callback lifetime outside tails not tested')
