#include "pci-retirement-owner.h"
#include "peer-table-owner.h"
#include "peer-close-executor.h"
#include "peer-open-owner.h"
#include "tasklet-schedule-owner.h"
#include <assert.h>
#include <string.h>
#define TRUE 1
#define FALSE 0
#define WDEV_NUM_MAX 1
typedef int BOOLEAN;typedef unsigned int UINT;typedef unsigned long ULONG;
typedef struct {
 int MacTabLock,wr_iot_transition_lock;
 int wr_iot_nettask_lock;unsigned int wr_iot_nettask_joined,wr_iot_nettask_release_claimed,wr_iot_nettask_initializing;
 struct wr_iot_tasklet_schedule_owner wr_iot_nettask_owner;
 struct wr_iot_pci_retirement wr_iot_pci_retirement;
 struct wr_child_teardown wr_iot_children;
 struct wr_iot_radio_transition wr_iot_transition;
 unsigned int wr_iot_registration_inflight;
 struct {unsigned int deferred_owners;} wr_iot_main_recovery;
 struct {unsigned int deferred_owners;} wr_iot_aux_family_retry;
 struct {int busy;} wr_iot_aux_family_retry_work;
 struct wr_iot_interface_ref wr_iot_interface_refs[2];
 struct wr_iot_peer_table_owner wr_iot_peer_table_owner;
 struct wr_iot_peer_close_executor wr_iot_peer_close_executor;
 struct wr_iot_peer_open_owner wr_iot_peer_open_owner;
 unsigned int wr_iot_peer_delete_active;unsigned long wr_iot_peer_close_serial;
} RTMP_ADAPTER;
static int held,inject_writer;static RTMP_ADAPTER *current;
#define RTMP_IRQ_LOCK(l,f) do{(void)(l);(f)=0;assert(!held);held=1;}while(0)
#define RTMP_IRQ_UNLOCK(l,f) do{(void)(l);(void)(f);assert(held==1);held=0;}while(0)
#define NdisAcquireSpinLock(l) do{(void)(l);assert(!held);held=2;if(inject_writer){inject_writer=0;current->wr_iot_peer_table_owner.transactions++;}}while(0)
#define NdisReleaseSpinLock(l) do{(void)(l);assert(held==2);held=0;}while(0)
#define work_busy(p) ((p)->busy)
#include "wr-iot-peer-adapter-release.inc"
static void ready(RTMP_ADAPTER *a){
 memset(a,0,sizeof *a);current=a;
 a->wr_iot_pci_retirement.phase=WR_PCI_RETIRE_RELEASE_CLAIMED;
 a->wr_iot_children.phase=WR_CHILD_DONE;
 wr_iot_radio_transition_init(&a->wr_iot_transition);
 a->wr_iot_transition.retiring=1;a->wr_iot_transition.shutdown_stage=2;
 a->wr_iot_transition.joined_workers=1U|4U;
#ifdef WSC_INCLUDED
 a->wr_iot_transition.joined_workers|=2;
#endif
 a->wr_iot_peer_table_owner.closed=1;
 wr_iot_tasklet_schedule_init(&a->wr_iot_nettask_owner);a->wr_iot_nettask_joined=1;
}
int main(void){RTMP_ADAPTER a;
 ready(&a);a.wr_iot_pci_retirement.phase=WR_PCI_RETIRE_FINAL_WORK_JOINED;
 assert(!wr_iot_adapter_release_begin(&a)&&!a.wr_iot_peer_table_owner.poisoned);
 ready(&a);a.wr_iot_transition.joined_workers=0;assert(!wr_iot_adapter_release_begin(&a));
 ready(&a);a.wr_iot_peer_delete_active=1;assert(!wr_iot_adapter_release_begin(&a));
 ready(&a);a.wr_iot_peer_table_owner.transactions=1;assert(!wr_iot_adapter_release_begin(&a));
 ready(&a);a.wr_iot_peer_table_owner.active=1;assert(!wr_iot_adapter_release_begin(&a));
 ready(&a);a.wr_iot_main_recovery.deferred_owners=1;assert(!wr_iot_adapter_release_begin(&a));
 ready(&a);a.wr_iot_aux_family_retry.deferred_owners=1;assert(!wr_iot_adapter_release_begin(&a));
 ready(&a);a.wr_iot_aux_family_retry_work.busy=1;assert(!wr_iot_adapter_release_begin(&a));
 ready(&a);a.wr_iot_interface_refs[0].published=1;assert(!wr_iot_adapter_release_begin(&a));
#ifdef WR_IOT_NETTASK_RELEASE_FENCE
 ready(&a);a.wr_iot_nettask_initializing=1;assert(!wr_iot_adapter_release_begin(&a));
 assert(!a.wr_iot_nettask_release_claimed);
 ready(&a);a.wr_iot_nettask_joined=0;assert(!wr_iot_adapter_release_begin(&a));
 assert(!a.wr_iot_nettask_release_claimed&&!a.wr_iot_peer_table_owner.poisoned);
 ready(&a);a.wr_iot_nettask_owner.blocked=0;assert(!wr_iot_adapter_release_begin(&a));
 ready(&a);a.wr_iot_nettask_owner.inflight=1;assert(!wr_iot_adapter_release_begin(&a));
 ready(&a);a.wr_iot_nettask_owner.poisoned=1;assert(!wr_iot_adapter_release_begin(&a));
 ready(&a);a.wr_iot_peer_delete_active=1;assert(!wr_iot_adapter_release_begin(&a));
 assert(a.wr_iot_nettask_release_claimed&&!a.wr_iot_peer_table_owner.poisoned);
 a.wr_iot_peer_delete_active=0;assert(wr_iot_adapter_release_begin(&a));
#endif
 ready(&a);inject_writer=1;assert(!wr_iot_adapter_release_begin(&a));
 assert(!a.wr_iot_peer_table_owner.poisoned&&a.wr_iot_peer_table_owner.transactions==1);
 ready(&a);assert(wr_iot_adapter_release_begin(&a)&&!held);
 assert(a.wr_iot_peer_table_owner.poisoned);
#ifdef WR_IOT_NETTASK_RELEASE_FENCE
 assert(a.wr_iot_nettask_release_claimed);
#endif
 assert(!wr_iot_peer_table_begin_open(&a.wr_iot_peer_table_owner));
 assert(!wr_iot_peer_table_transaction_enter(&a.wr_iot_peer_table_owner));
 assert(!wr_iot_adapter_release_begin(&a)&&!held);
 return 0;
}
