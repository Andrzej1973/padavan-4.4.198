#include "pci-retirement-owner.h"
#include "main-open-recovery-owner.h"
#include <assert.h>
#include <stddef.h>
#include <stdio.h>

typedef unsigned long ULONG;
struct work_struct { int pending; };
struct delayed_work { struct work_struct work; };
typedef struct adapter {
 int wr_iot_transition_lock;
 struct wr_iot_pci_retirement wr_iot_pci_retirement;
 struct wr_iot_main_recovery_owner wr_iot_main_recovery;
 struct work_struct wr_iot_main_recovery_work;
 struct delayed_work wr_iot_main_recovery_reap_work;
} RTMP_ADAPTER,*PRTMP_ADAPTER;
static int locked,flushes,mode;
#define RTMP_IRQ_LOCK(lock,flags) ((void)(lock),(flags)=0,assert(!locked),locked=1)
#define RTMP_IRQ_UNLOCK(lock,flags) ((void)(lock),(void)(flags),assert(locked),locked=0)
static int flush_delayed_work(struct delayed_work *work){
 assert(work&&!locked);flushes++;
 if(mode==0 && flushes==2){
  RTMP_ADAPTER *ad=(RTMP_ADAPTER *)((char *)work-
    offsetof(RTMP_ADAPTER,wr_iot_main_recovery_reap_work));
  ad->wr_iot_main_recovery.deferred_owners=0;
  work->work.pending=0;
 }
 if(mode==3 && flushes==2)work->work.pending=0;
 if(mode==1)work->work.pending=0;
 return 1;
}
static int flush_work(struct work_struct *work){assert(work&&!locked);return 1;}
static int wr_iot_main_recovery_join_complete(RTMP_ADAPTER *ad){
 assert(ad&&!locked);return 0;
}
static int delayed_work_pending(struct delayed_work *work){return work->work.pending;}
static int work_busy(struct work_struct *work){return work->pending;}

#include "pci-recovery-drain.inc"

static void setup(RTMP_ADAPTER *ad,int test_mode){
 *ad=(RTMP_ADAPTER){0};mode=test_mode;flushes=locked=0;
 wr_iot_pci_retirement_init(&ad->wr_iot_pci_retirement);
 ad->wr_iot_pci_retirement.phase=WR_PCI_RETIRE_DRAINING;
 ad->wr_iot_main_recovery.deferred_owners=1;
 ad->wr_iot_main_recovery_reap_work.work.pending=1;
}
int main(void){
 RTMP_ADAPTER ad;
 setup(&ad,0);
 assert(wr_iot_pci_recovery_drain(&ad));
 assert(flushes==2&&!locked&&
        ad.wr_iot_pci_retirement.phase==WR_PCI_RETIRE_DRAINED);
 setup(&ad,1);
 assert(!wr_iot_pci_recovery_drain(&ad));
 assert(flushes==1&&!locked&&
        ad.wr_iot_pci_retirement.phase==WR_PCI_RETIRE_DRAINING);
 setup(&ad,2);
 assert(!wr_iot_pci_recovery_drain(&ad));
 assert(flushes==4&&!locked&&
        ad.wr_iot_pci_retirement.phase==WR_PCI_RETIRE_DRAINING);
 setup(&ad,3);
 ad.wr_iot_main_recovery.deferred_owners=0;
 assert(wr_iot_pci_recovery_drain(&ad));
 assert(flushes==2&&!locked&&
        ad.wr_iot_pci_retirement.phase==WR_PCI_RETIRE_DRAINED);
 puts("PASS isolated PCI drain: completion, no next work, bounded self-rearm, queued callback after owner completion");
 return 0;
}
