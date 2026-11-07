#!/usr/bin/env python3
"""Execute extracted joined-rearm ordering with injected kernel operations."""
import argparse
from pathlib import Path
import subprocess
import tempfile
p=argparse.ArgumentParser(description=__doc__)
p.add_argument("candidate",type=Path)
a=p.parse_args()
s=(a.candidate/"common/rtmp_init.c").read_text()
start=s.index("INT wr_iot_aux_family_retry_rearm_joined(")
brace=s.index("{",start);depth=1;end=brace+1
while depth:
 depth+=(s[end]=="{")-(s[end]=="}");end+=1
fn=s[start:end]
prefix=r"""
#include <assert.h>
#include <stdio.h>
#include "aux-family-retry-scheduler.h"
typedef int INT;typedef unsigned long ULONG;
#define EBUSY 16
#define WDEV_NUM_MAX 0
struct work_struct { int unused; };
typedef struct {
 struct work_struct wr_iot_aux_family_retry_work;
 int wr_iot_transition_lock;
 struct { int retiring; } wr_iot_transition;
 struct wr_iot_aux_retry_owner wr_iot_aux_family_retry;
 struct wr_iot_interface_ref wr_iot_interface_refs[1];
 struct wr_iot_family_close wr_iot_family_close[1];
} RTMP_ADAPTER;
static int held,flushed,busy,accept,schedules;
#define RTMP_IRQ_LOCK(lock,flags) do { (void)(lock);(flags)=0;assert(!held&&flushed);held=1; } while(0)
#define RTMP_IRQ_UNLOCK(lock,flags) do { (void)(lock);(void)(flags);assert(held);held=0; } while(0)
static void flush_work(struct work_struct *work){(void)work;assert(!held);flushed=1;}
static int work_busy(struct work_struct *work){(void)work;assert(held);return busy;}
static int schedule_work(struct work_struct *work){(void)work;assert(held);schedules++;return accept;}
static struct wr_iot_interface_ref *wr_iot_registry_find(struct wr_iot_interface_ref *r,unsigned int count,const void *dev,unsigned long generation){
 assert(held&&count==1);return r->device==dev&&r->generation==generation?r:0;
}
"""
suffix=r"""
static void setup(RTMP_ADAPTER *ad,int *dev){
 struct wr_iot_interface_ref *r=&ad->wr_iot_interface_refs[0];
 struct wr_iot_family_close *s=&ad->wr_iot_family_close[0];
 *ad=(RTMP_ADAPTER){0};held=flushed=busy=schedules=0;accept=1;
 wr_iot_ref_init(r,dev,1);wr_iot_family_close_init(s);
 r->published=1;r->phase=WR_REF_CLOSING;r->family=WR_REF_FAMILY_APCLI;
 r->close_stage=1;r->close_serial=3;r->close_epoch=2;r->last_token=4;
 s->device=dev;s->generation=1;s->serial=3;s->epoch=2;s->token=4;
 s->family=WR_REF_FAMILY_APCLI;s->phase=WR_FAMILY_DOWN_RETRY;
 wr_iot_aux_retry_init(&ad->wr_iot_aux_family_retry);
 assert(wr_iot_aux_retry_queue(&ad->wr_iot_aux_family_retry,r,s,1,1,1));
 assert(wr_iot_aux_retry_schedule_result(&ad->wr_iot_aux_family_retry,0));
}
int main(void){
 RTMP_ADAPTER ad;int dev;
 assert(wr_iot_aux_family_retry_rearm_joined(0)==-EBUSY);
 setup(&ad,&dev);assert(wr_iot_aux_family_retry_rearm_joined(&ad)==0&&schedules==1&&!held);
 setup(&ad,&dev);ad.wr_iot_transition.retiring=1;
 assert(wr_iot_aux_family_retry_rearm_joined(&ad)==-EBUSY&&!schedules);
 setup(&ad,&dev);busy=1;assert(wr_iot_aux_family_retry_rearm_joined(&ad)==-EBUSY&&!schedules);
 setup(&ad,&dev);ad.wr_iot_interface_refs[0].generation++;
 assert(wr_iot_aux_family_retry_rearm_joined(&ad)==-EBUSY&&!schedules);
 setup(&ad,&dev);accept=0;assert(wr_iot_aux_family_retry_rearm_joined(&ad)==-EBUSY&&schedules==1);
 assert(ad.wr_iot_aux_family_retry.phase==WR_AUX_RETRY_RETAINED&&ad.wr_iot_aux_family_retry.netdev_held);
 puts("PASS extracted joined rearm lock order, refusal gates and failed submission retention");
}
"""
with tempfile.TemporaryDirectory(prefix="wr-joined-rearm-") as directory:
 root=Path(directory);source=root/"check.c";binary=root/"check";source.write_text(prefix+fn+suffix)
 subprocess.run(["gcc","-std=c11","-Wall","-Wextra","-Werror","-fsanitize=address,undefined","-I"+str(a.candidate/"include"),str(source),"-o",str(binary)],check=True)
 subprocess.run([str(binary)],check=True)

# Compile/run the exact remove entry prefix; no actual PCI operation occurs.
pci=(a.candidate/"os/linux/pci_main_dev.c").read_text()
start=pci.index("static VOID DEVEXIT rt_pci_remove(")
end=pci.index("DBGPRINT(",start)
entry=pci[start:end]+"(void)csr_addr;(void)pAd;\n}\n"
entry_prefix=r"""
#include <assert.h>
#include <stddef.h>
#define VOID void
#define DEVEXIT
struct net_device { unsigned long base_addr; };
struct pci_dev { struct net_device *data; };
typedef struct net_device *PNET_DEV;
typedef unsigned long ULONG;
static int reads;
static struct net_device *pci_get_drvdata(struct pci_dev *p){return p->data;}
#define GET_PAD_FROM_NET_DEV(ad,dev) do {assert(dev);reads++;ad=dev;}while(0)
"""
entry_suffix="int main(void){struct pci_dev p={0};struct net_device d={1};rt_pci_remove(&p);assert(!reads);p.data=&d;rt_pci_remove(&p);assert(reads==1);return 0;}\n"
with tempfile.TemporaryDirectory(prefix="wr-pci-entry-") as directory:
 root=Path(directory);source=root/"check.c";binary=root/"check"
 source.write_text(entry_prefix+entry+entry_suffix)
 subprocess.run(["gcc","-std=c11","-Wall","-Wextra","-Werror","-fsanitize=address,undefined",str(source),"-o",str(binary)],check=True)
 subprocess.run([str(binary)],check=True)
print("PASS extracted PCI remove entry rejects absent netdev before dereference")

# Normal ndo_open runs synchronously under RTNL in pinned kernel. Keep its
# barrier after admission retirement and outside every recovery wait.
pci=(a.candidate/'os/linux/pci_main_dev.c').read_text()
remove=pci[pci.index('static VOID DEVEXIT rt_pci_remove('):]
retire=remove.index('wr_iot_radio_retire(')
lock=remove.index('RtmpOSNetDevProtect(1);')
unlock=remove.index('RtmpOSNetDevProtect(0);',lock)
drain=remove.index('if (!wr_iot_pci_recovery_drain(adapter))')
begin=remove.index("if (!wr_iot_pci_retirement_begin(")
assert retire<lock<unlock<begin<drain
assert "RTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock, flags);" in remove[retire:lock]
assert "RTMP_IRQ_LOCK(&adapter->wr_iot_transition_lock, flags);" in remove[unlock:begin]
between=remove[lock+len('RtmpOSNetDevProtect(1);'):unlock]
assert not any(word in between for word in
               ['flush_work','cancel_work','wait_event','return','goto'])
assert not between.strip(), 'RTNL callback barrier must release immediately'
print('PASS PCI OPEN barrier: admission retired, RTNL released before recovery drain; source ordering only')

aux_stop=remove.index('wr_iot_aux_retry_request_stop(&adapter->wr_iot_aux_family_retry)')
stop_cancel=remove.index('cancel_work_sync(&adapter->wr_iot_aux_family_retry_work);')
assert drain<aux_stop<stop_cancel
print('PASS auxiliary stop admission precedes worker cancellation')

# STALLED closes admission for both recovery domains before joining callbacks.
start=remove.index('if (!wr_iot_pci_recovery_drain(adapter)) {')
end=remove.index('return; /* Retained owners; terminal DMA/IRQ fence still required. */',start)
stalled=remove[start:end]
main=stalled.index('wr_iot_main_recovery_request_stop(')
aux=stalled.index('wr_iot_aux_retry_request_stop(')
released=stalled.index('RTMP_IRQ_UNLOCK(')
reaper=stalled.index('cancel_delayed_work_sync(')
worker=stalled.index('cancel_work_sync(&adapter->wr_iot_main_recovery_work);')
auxworker=stalled.index('cancel_work_sync(&adapter->wr_iot_aux_family_retry_work);')
assert main<aux<released<reaper<worker<auxworker
assert not any(x in stalled for x in ['dev_put(', 'RtmpRaDevCtrlExit(', 'iounmap(', 'RtmpOSNetDevFree('])
print('PASS STALLED: both stop intents precede unlocked work joins; no retained resource free')
