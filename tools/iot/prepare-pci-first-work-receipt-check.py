#!/usr/bin/env python3
"""Extract actual first-join block; work callbacks/kernel locks modeled."""
import argparse
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('candidate',type=Path);p.add_argument('output',type=Path)
a=p.parse_args()
if a.output.exists():p.error('new fixture output required')
s=(a.candidate/'os/linux/pci_main_dev.c').read_text();start=s.index('static VOID DEVEXIT rt_pci_remove(')
s=s[start:s.index('\n}',start)+2]
start=s.index('\t\tcancel_delayed_work_sync(')
end=s.index('\t\t/* A failed child detach',start)
if '\t\tif (!wr_iot_pci_children_begin(adapter)) return;' in s:
 end=s.index('\t\tif (!wr_iot_pci_children_begin(adapter)) return;',start)
 assert s.index('wr_iot_pci_retirement_work_joined(')<end<s.index('RtmpPhyNetDevExit(pAd, net_dev)')
block=s[start:end]
main_cancel=block.index('cancel_work_sync(&adapter->wr_iot_main_recovery_work)')
aux_cancel=block.index('cancel_work_sync(&adapter->wr_iot_aux_family_retry_work)')
joined_receipt=block.index('wr_iot_pci_retirement_work_joined')
assert block.index('cancel_delayed_work_sync')<main_cancel<aux_cancel<joined_receipt
assert 'if (!wr_iot_pci_retirement_stop_requested(' in s
prefix=r'''
#include "pci-retirement-owner.h"
#include <assert.h>
#include <string.h>
typedef unsigned long ULONG;
typedef struct {int wr_iot_transition_lock,wr_iot_main_recovery_reap_work,wr_iot_main_recovery_work;
 struct {int busy;} wr_iot_aux_family_retry_work;
 struct {int stop_requested;unsigned int deferred_owners;} wr_iot_main_recovery;
 struct {unsigned int deferred_owners;} wr_iot_aux_family_retry;
 struct wr_iot_pci_retirement wr_iot_pci_retirement;} RTMP_ADAPTER;
static int held,delayed,ordinary,joined,reached_child,inject_owner;
#define cancel_delayed_work_sync(p) do{(void)(p);assert(!held);delayed++;}while(0)
#define cancel_work_sync(p) do{(void)(p);assert(!held);ordinary++;}while(0)
#define work_busy(p) ((p)->busy)
#define RTMP_IRQ_LOCK(l,f) do{(void)(l);(f)=0;assert(!held);held=1;}while(0)
#define RTMP_IRQ_UNLOCK(l,f) do{(void)(l);(void)(f);assert(held);held=0;}while(0)
static void wr_iot_main_recovery_join_complete(RTMP_ADAPTER *a){
 assert(!held&&delayed>0&&ordinary>=delayed);joined++;
 if(inject_owner)a->wr_iot_main_recovery.deferred_owners=1;
}
static void first_join(RTMP_ADAPTER *adapter){ULONG flags;
'''
post=r'''
 reached_child++;
}
int main(void){RTMP_ADAPTER a={0};
a.wr_iot_pci_retirement.phase=WR_PCI_RETIRE_STOP_REQUESTED;
first_join(&a);assert(!reached_child&&a.wr_iot_pci_retirement.phase==WR_PCI_RETIRE_STOP_REQUESTED);
a.wr_iot_main_recovery.stop_requested=1;inject_owner=1;
first_join(&a);assert(!reached_child&&a.wr_iot_pci_retirement.phase==WR_PCI_RETIRE_STOP_REQUESTED);
inject_owner=0;a.wr_iot_main_recovery.deferred_owners=0;
a.wr_iot_aux_family_retry.deferred_owners=1;
first_join(&a);assert(!reached_child&&a.wr_iot_pci_retirement.phase==WR_PCI_RETIRE_STOP_REQUESTED);
a.wr_iot_aux_family_retry.deferred_owners=0;
a.wr_iot_aux_family_retry_work.busy=1;
first_join(&a);assert(!reached_child&&a.wr_iot_pci_retirement.phase==WR_PCI_RETIRE_STOP_REQUESTED);
a.wr_iot_aux_family_retry_work.busy=0;
first_join(&a);assert(reached_child==1&&a.wr_iot_pci_retirement.phase==WR_PCI_RETIRE_WORK_JOINED);
first_join(&a);assert(reached_child==1); /* Cannot replay receipt. */
assert(delayed==6&&ordinary==12&&joined==6&&!held);
return 0;}
'''
a.output.write_text(prefix+block+post,encoding='utf-8')
print('Extracted actual first work-join block; no child/root callback or DMA acceptance')
