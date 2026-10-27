#include <assert.h>
#include "mbss-close-evidence.h"

typedef int INT;
typedef unsigned int UINT;
typedef unsigned long ULONG;
#define WDEV_NUM_MAX 4
#define FIRST_MBSSID 1
#define NDIS_STATUS_SUCCESS 0
#define NDIS_STATUS_FAILURE 1
#define MAX_MBSSID_NUM(ad) ((ad)->max_bss)
static int held;
#define RTMP_IRQ_LOCK(lock, flags) do { (void)(lock); (flags)=0; assert(!held); held=1; } while(0)
#define RTMP_IRQ_UNLOCK(lock, flags) do { (void)(lock); (void)(flags); assert(held); held=0; } while(0)
typedef struct {
 struct { struct { struct { void *if_dev; } wdev; } MBSSID[WDEV_NUM_MAX]; } ApCfg;
 struct { unsigned int retiring, active_tx; } wr_iot_transition;
 int wr_iot_transition_lock;
 unsigned int wr_iot_registration_inflight, wr_iot_pci_work_joined;
 unsigned int max_bss;
 struct wr_iot_interface_ref wr_iot_interface_refs[WDEV_NUM_MAX+1];
} RTMP_ADAPTER;
#include "mbss-global-preflight.inc"

static void record(struct wr_iot_interface_ref *r, void *dev,
 enum wr_iot_ref_family family){
 wr_iot_ref_init(r,dev,1);
 r->family=family;r->published=1;
}

int main(void){
 RTMP_ADAPTER ad={0};
 int main_dev=0,bss1=0,bss2=0;
 struct wr_iot_interface_ref *r=ad.wr_iot_interface_refs;
 ad.max_bss=3;
 ad.ApCfg.MBSSID[1].wdev.if_dev=&bss1;
 ad.ApCfg.MBSSID[2].wdev.if_dev=&bss2;
 ad.wr_iot_transition.retiring=1;
 ad.wr_iot_pci_work_joined=1;
 record(&r[0],&main_dev,WR_REF_FAMILY_MAIN);
 record(&r[1],&bss1,WR_REF_FAMILY_MBSS);
 record(&r[2],&bss2,WR_REF_FAMILY_MBSS);
 r[1].last_token=r[2].last_token=1;
 r[1].close_stage=r[2].close_stage=4;
 assert(wr_iot_mbss_global_preflight(&ad)==NDIS_STATUS_SUCCESS&&!held);
 r[2].phase=WR_REF_OWNED;
 assert(wr_iot_mbss_global_preflight(&ad)==NDIS_STATUS_FAILURE&&!held);
 r[2].phase=WR_REF_CLOSING;
 assert(wr_iot_mbss_global_preflight(&ad)==NDIS_STATUS_FAILURE&&!held);
 r[2].phase=WR_REF_IDLE;r[2].close_stage=3;
 assert(wr_iot_mbss_global_preflight(&ad)==NDIS_STATUS_FAILURE&&!held);
 r[2].close_stage=4;
 ad.ApCfg.MBSSID[2].wdev.if_dev=0;
 assert(wr_iot_mbss_global_preflight(&ad)==NDIS_STATUS_FAILURE&&!held);
 ad.ApCfg.MBSSID[2].wdev.if_dev=&bss2;
 ad.wr_iot_pci_work_joined=0;
 assert(wr_iot_mbss_global_preflight(&ad)==NDIS_STATUS_FAILURE&&!held);
 ad.wr_iot_pci_work_joined=1;
 ad.wr_iot_registration_inflight=1;
 assert(wr_iot_mbss_global_preflight(&ad)==NDIS_STATUS_FAILURE&&!held);
 ad.wr_iot_registration_inflight=0;ad.wr_iot_transition.active_tx=1;
 assert(wr_iot_mbss_global_preflight(&ad)==NDIS_STATUS_FAILURE&&!held);
 ad.wr_iot_transition.active_tx=0;ad.wr_iot_transition.retiring=0;
 assert(wr_iot_mbss_global_preflight(&ad)==NDIS_STATUS_FAILURE&&!held);
 ad.wr_iot_transition.retiring=1;r[2].family=WR_REF_FAMILY_UNKNOWN;
 assert(wr_iot_mbss_global_preflight(&ad)==NDIS_STATUS_FAILURE&&!held);
 r[2].family=WR_REF_FAMILY_MBSS;ad.max_bss=WDEV_NUM_MAX+1;
 assert(wr_iot_mbss_global_preflight(&ad)==NDIS_STATUS_FAILURE&&!held);
 return 0;
}
