#include <assert.h>
#include <stddef.h>
#include "interface-registry.h"
#define WDS_SUPPORT 1
#define ENTRY_WDS 2
#define WDEV_NUM_MAX 2
typedef unsigned int UINT;typedef unsigned long ULONG;typedef int INT;
struct wifi_dev {void *if_dev;};
struct adapter {int MacTabLock,wr_iot_transition_lock;struct {int retiring,pm_suspending,pm_suspended;} wr_iot_transition;struct wr_iot_interface_ref wr_iot_interface_refs[3];};
static int mac,transition,inserted,mark_before_check;
#define RTMP_IRQ_LOCK(l,f) do{(void)(l);(f)=0;assert(mac&&!transition);transition=1;if(mark_before_check)pAd->wr_iot_interface_refs[0].removing=1;}while(0)
#define RTMP_IRQ_UNLOCK(l,f) do{(void)(l);(void)(f);assert(mac&&transition);transition=0;}while(0)
#define NdisReleaseSpinLock(l) do{(void)(l);assert(mac&&!transition);mac=0;}while(0)
static void *insert(struct adapter *pAd,struct wifi_dev *wdev,int ent_type){
#include "wds-insertion-gate.inc"
assert(mac&&!transition);inserted++;return wdev;
}
static void reset(struct adapter *a,void *dev){*a=(struct adapter){0};a->wr_iot_interface_refs[0].device=dev;a->wr_iot_interface_refs[0].generation=1;a->wr_iot_interface_refs[0].family=WR_REF_FAMILY_WDS;a->wr_iot_interface_refs[0].published=1;mac=1;transition=inserted=mark_before_check=0;}
int main(void){struct adapter a;int dev;struct wifi_dev w={&dev};
reset(&a,&dev);assert(insert(&a,&w,ENTRY_WDS)==&w&&inserted==1&&mac);
reset(&a,&dev);a.wr_iot_interface_refs[0].removing=1;assert(!insert(&a,&w,ENTRY_WDS)&&!mac&&!inserted);
reset(&a,&dev);mark_before_check=1;assert(!insert(&a,&w,ENTRY_WDS)&&!mac&&!inserted);
reset(&a,&dev);a.wr_iot_transition.retiring=1;assert(!insert(&a,&w,ENTRY_WDS)&&!mac);
reset(&a,&dev);a.wr_iot_transition.pm_suspending=1;assert(!insert(&a,&w,ENTRY_WDS)&&!mac);
reset(&a,&dev);a.wr_iot_interface_refs[0].generation=0;assert(!insert(&a,&w,ENTRY_WDS)&&!mac);
reset(&a,&dev);a.wr_iot_interface_refs[0].family=WR_REF_FAMILY_MBSS;assert(!insert(&a,&w,ENTRY_WDS)&&!mac);
reset(&a,&dev);a.wr_iot_interface_refs[0].removing=1;assert(insert(&a,&w,1)==&w&&mac&&inserted);
return 0;}
