#!/usr/bin/env python3
"""Extract final publication blocks and check source initialization ordering."""
import argparse
from pathlib import Path

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('candidate', type=Path)
p.add_argument('output', type=Path)
a = p.parse_args()
if a.output.exists():
    p.error('new output required')
s = (a.candidate / 'mgmt/mgmt_entrytb.c').read_text()
marker = '/* Publish initialized TR queues under their admission lock. */'
blocks = []
for name in ['tr_tb_set_entry', 'tr_tb_set_mcast_entry']:
    begin = s.index('VOID ' + name + '(')
    end = s.index('\n}', begin) + 2
    body = s[begin:end]
    assert body.count(marker) == 1
    pub = body.index(marker)
    for init in ['InitializeQueueHeader(&tr_entry->ps_queue)',
                 'NdisAllocateSpinLock(pAd, &tr_entry->ps_queue_lock)',
                 'tr_entry->PsTokenFlag = 0', 'NdisMoveMemory(tr_entry->bssid',
                 'tr_entry->high_pkt_cnt = 0', 'tr_entry->high_pkt_drop_cnt = 0']:
        assert body.index(init) < pub, (name, init)
    assert 'tr_entry->enq_cap = TRUE;' not in body
    lock_end = body.index('RTMP_IRQ_UNLOCK', pub)
    close = body.index('}', lock_end) + 1
    blocks.append(body[pub:close])
prefix = r'''
#include <assert.h>
#define TRUE 1
typedef unsigned long ULONG;
typedef struct {int enq_cap,deq_cap;} TR;
typedef struct {int irq_lock;} ADAPTER;
static int held,stores,initialized;
#define WRITE_ONCE(x,v) do{assert(held&&initialized);(x)=(v);stores++;}while(0)
#define RTMP_IRQ_LOCK(l,f) do{(void)(l);(f)=0;assert(!held);held=1;}while(0)
#define RTMP_IRQ_UNLOCK(l,f) do{(void)(l);(void)(f);assert(held&&stores==2);held=0;}while(0)
'''
functions = ''.join('static void publish%d(ADAPTER *pAd,TR *tr_entry){\n%s\n}\n' % (i,b)
                    for i,b in enumerate(blocks))
suffix = r'''
int main(void){ADAPTER a={0};TR t={0};initialized=1;
publish0(&a,&t);assert(!held&&t.enq_cap&&t.deq_cap);
t=(TR){0};stores=0;publish1(&a,&t);assert(!held&&t.enq_cap&&t.deq_cap);return 0;}
'''
a.output.write_text(prefix + functions + suffix, encoding='utf-8')
print('PASS source initialization order; extracted two publication blocks (caller lifetime unproved)')
