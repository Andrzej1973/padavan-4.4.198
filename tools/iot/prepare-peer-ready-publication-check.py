#!/usr/bin/env python3
"""Extract caller publication; verify initialization order, not hardware success."""
import argparse
from pathlib import Path

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('candidate', type=Path); p.add_argument('output', type=Path)
a = p.parse_args()
if a.output.exists():
    p.error('new output required')
s = (a.candidate/'mgmt/mgmt_entrytb.c').read_text()
start = s.index('BOOLEAN tr_tb_set_entry(')
end = s.index('VOID tr_tb_set_mcast_entry(', start)
assert 'WRITE_ONCE(tr_entry->enq_cap, TRUE)' not in s[start:end]
assert 'WRITE_ONCE(tr_entry->enq_cap, FALSE)' in s[start:end]
private='static MAC_TABLE_ENTRY *wr_iot_mac_insert_entry('
start = s.index(private if private in s else 'MAC_TABLE_ENTRY *MacTableInsertEntry(')
end = s.index('INT mac_tb_del_from_hash(', start)
body = s[start:end]
marker = '/* Publish peer admission only after insertion initialization. */'
assert body.count(marker) == 1
point = body.index(marker)
hardware_init=('#include "wr-iot-peer-hardware-insert-result.inc"' if
               '#include "wr-iot-peer-hardware-insert-result.inc"' in body else 'RTMP_STA_ENTRY_ADD(pAd, pEntry);')
for init in ['UAPSD_MR_ENTRY_INIT(pEntry);', 'RTMPInitTimer',
             '/* add this MAC entry into HASH table */', hardware_init]:
    assert body.index(init) < point, init
block = body[point:body.index('NdisReleaseSpinLock(&pAd->MacTabLock);', point)]
prefix = r'''
#include <assert.h>
#define TRUE 1
typedef unsigned long ULONG;
struct tr {int enq_cap,deq_cap;};struct ad {int irq_lock;};
static int held,irq,ready,stores;
#define RTMP_IRQ_LOCK(l,f) do{(void)(l);(f)=0;assert(held&&!irq);irq=1;}while(0)
#define RTMP_IRQ_UNLOCK(l,f) do{(void)(l);(void)(f);assert(irq);irq=0;}while(0)
#define WRITE_ONCE(x,v) do{assert(irq&&ready);(x)=(v);stores++;}while(0)
static void publish(struct ad *pAd,struct tr *tr_entry,void *pEntry){
'''
suffix = r'''
}
int main(void){struct ad a={0};struct tr tr={0};held=1;
publish(&a,&tr,0);assert(!stores&&!tr.enq_cap&&!irq);
ready=1;publish(&a,&tr,&tr);assert(stores==2&&tr.enq_cap&&tr.deq_cap&&!irq);return 0;}
'''
a.output.write_text(prefix+block+suffix, encoding='utf-8')
print('PASS initialization ordering; hardware return status and callback readiness unproved')
