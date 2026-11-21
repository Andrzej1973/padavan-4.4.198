#include "interface-registry.h"
#include <assert.h>
static int held;
static void pin(const void *device){assert(device);held++;}
static void unpin(const void *device){assert(device&&held>0);held--;}
int main(void){
 struct wr_iot_interface_ref slots[2]={0},*a,*b;unsigned long seq=0,old;int d1=0,d2=0,d3=0;
 const void *snapshot[2]={0};int n;
 a=wr_iot_registry_add(slots,2,&seq,&d1);assert(a&&seq==1);old=a->generation;a->published=1;
 assert(wr_iot_registry_find_openable(slots,2,&d1)==a);
 assert(!wr_iot_registry_add(slots,2,&seq,&d1)&&seq==1);
 b=wr_iot_registry_add(slots,2,&seq,&d2);assert(b&&seq==2);
 assert(!wr_iot_registry_find_openable(slots,2,&d2));
 assert(wr_iot_registry_snapshot(slots,2,snapshot,1,pin)==-1&&!held);
 n=wr_iot_registry_snapshot(slots,2,snapshot,2,pin);
 assert(n==1&&snapshot[0]==&d1&&held==1);
 unpin(snapshot[0]);assert(!held);
 assert(!wr_iot_registry_add(slots,2,&seq,&d3)&&seq==2);
 assert(wr_iot_registry_find(slots,2,&d1,old)==a);
 assert(wr_iot_ref_reserve(a,&d1,old,1));assert(!wr_iot_registry_release(a,&d1,old));
 assert(!wr_iot_registry_find_openable(slots,2,&d1));
 assert(!wr_iot_registry_begin_remove(a,&d1,old)&&!a->removing);
 assert(wr_iot_ref_open_finish(a,&d1,old,1,1));assert(!wr_iot_registry_release(a,&d1,old));
 assert(!wr_iot_registry_find_openable(slots,2,&d1));
 assert(wr_iot_ref_begin_close(a,&d1,old,1));assert(!wr_iot_registry_release(a,&d1,old));
 assert(!wr_iot_registry_begin_remove(a,&d1,old)&&!a->removing);
 assert(wr_iot_registry_snapshot(slots,2,snapshot,2,pin)==1&&held==1);
 unpin(snapshot[0]);assert(!held);
 assert(wr_iot_ref_consume(a,&d1,old,1));assert(!wr_iot_registry_release(a,&d1,old));
 assert(wr_iot_registry_begin_remove(a,&d1,old));
 assert(!wr_iot_registry_find_openable(slots,2,&d1));
 assert(!wr_iot_ref_reserve(a,&d1,old,2));
 assert(!wr_iot_registry_vendor_done(a,&d1,old));
 assert(wr_iot_registry_kernel_done(a,&d1,old));
 assert(!wr_iot_registry_kernel_done(a,&d1,old));
 assert(!wr_iot_registry_release(a,&d1,old));
 assert(wr_iot_registry_vendor_done(a,&d1,old));
 assert(wr_iot_registry_release(a,&d1,old));
 a=wr_iot_registry_add(slots,2,&seq,&d1);assert(a&&seq==3&&a->generation!=old);
 assert(!wr_iot_registry_find_openable(slots,2,&d1));
 assert(!wr_iot_registry_find(slots,2,&d1,old));assert(!wr_iot_registry_release(a,&d1,old));
 assert(!wr_iot_ref_reserve(a,&d1,old,2));
 assert(wr_iot_registry_release(a,&d1,a->generation));seq=~0UL;
 assert(!wr_iot_registry_add(slots,2,&seq,&d3)&&seq==~0UL);
 {struct wr_iot_interface_ref retry={0};int retrydev=0;
  wr_iot_ref_init(&retry,&retrydev,41);retry.published=1;
  assert(wr_iot_ref_reserve(&retry,&retrydev,41,1));
  assert(!wr_iot_registry_begin_remove(&retry,&retrydev,41)&&!retry.removing);
  assert(wr_iot_ref_open_finish(&retry,&retrydev,41,1,0));
  assert(wr_iot_registry_begin_remove(&retry,&retrydev,41));
  assert(!wr_iot_registry_cancel_remove_unmutated(&retry,&retrydev,40,0));
  assert(!wr_iot_registry_cancel_remove_unmutated(&retry,&retrydev,41,1));
  assert(retry.removing);
  assert(wr_iot_registry_cancel_remove_unmutated(&retry,&retrydev,41,0));
  assert(!retry.removing&&retry.published);
  assert(wr_iot_registry_begin_remove(&retry,&retrydev,41));
  assert(wr_iot_registry_kernel_done(&retry,&retrydev,41));
  assert(!wr_iot_registry_cancel_remove_unmutated(&retry,&retrydev,41,0));
 }
 {struct wr_iot_interface_ref uncertain={0};int uncertain_dev=0;
  wr_iot_ref_init(&uncertain,&uncertain_dev,42);uncertain.published=1;
  assert(wr_iot_ref_reserve(&uncertain,&uncertain_dev,42,1));
  assert(wr_iot_ref_open_uncertain(&uncertain,&uncertain_dev,42,1));
  assert(!wr_iot_registry_begin_remove(&uncertain,&uncertain_dev,42));
  assert(!wr_iot_registry_release(&uncertain,&uncertain_dev,42));
 }
 {struct wr_iot_interface_ref detached={0};int detached_dev=0;
  wr_iot_ref_init(&detached,&detached_dev,43);detached.published=1;
  assert(wr_iot_registry_begin_remove(&detached,&detached_dev,43));
  detached.phase=WR_REF_OWNED;
  assert(!wr_iot_registry_release_after_detach(&detached,&detached_dev,43,
          1,1,1,1));
  assert(detached.removal_stage==1&&detached.device==&detached_dev);
  detached.phase=WR_REF_IDLE;
  assert(!wr_iot_registry_release_after_detach(&detached,&detached_dev,43,
          0,0,1,1));
  assert(!wr_iot_registry_release_after_detach(&detached,&detached_dev,43,
          1,0,1,1));
  assert(!wr_iot_registry_release_after_detach(&detached,&detached_dev,43,
          1,1,0,1));
  assert(detached.removal_stage==1&&detached.device==&detached_dev);
  detached.last_token=1;
  assert(!wr_iot_registry_release_after_detach(&detached,&detached_dev,43,
          1,1,1,1));
  detached.family=WR_REF_FAMILY_MBSS;
  detached.close_stage=4;
  assert(!wr_iot_registry_release_after_detach(&detached,&detached_dev,44,
          1,1,1,1));
  assert(!wr_iot_registry_release_after_detach(&detached,&detached_dev,43,
          1,1,1,0));
  assert(detached.removal_stage==1&&detached.device==&detached_dev);
  assert(wr_iot_registry_release_after_detach(&detached,&detached_dev,43,
          1,1,1,1));
  assert(!detached.device&&!detached.published);
  assert(!wr_iot_registry_release_after_detach(&detached,&detached_dev,43,
          1,1,1,1));
 }
 {struct wr_iot_interface_ref wds={0};int dev=0;
  wr_iot_ref_init(&wds,&dev,45);wds.published=1;
  wds.family=WR_REF_FAMILY_WDS;
  assert(wr_iot_registry_begin_remove(&wds,&dev,45));
  wds.last_token=1;wds.close_stage=4;
  assert(!wr_iot_registry_release_after_detach(&wds,&dev,45,1,1,1,0));
  wds.close_stage=2;
  assert(wr_iot_registry_release_after_detach(&wds,&dev,45,1,1,1,0));
 }
 {struct wr_iot_interface_ref aux={0};int dev=0;
  wr_iot_ref_init(&aux,&dev,46);aux.published=1;
  aux.family=WR_REF_FAMILY_APCLI;
  assert(wr_iot_registry_begin_remove(&aux,&dev,46));
  aux.last_token=1;aux.close_stage=2;
  assert(!wr_iot_registry_release_after_detach(&aux,&dev,46,1,1,1,1));
  aux.family=WR_REF_FAMILY_MONITOR;
  assert(!wr_iot_registry_release_after_detach(&aux,&dev,46,1,1,1,1));
  aux.family=WR_REF_FAMILY_UNKNOWN;
  assert(!wr_iot_registry_release_after_detach(&aux,&dev,46,1,1,1,1));
 }
 {struct wr_iot_interface_ref pending={0};int dev=0;
  wr_iot_ref_init(&pending,&dev,47);pending.published=1;
  pending.family=WR_REF_FAMILY_MBSS;
  assert(wr_iot_registry_begin_remove(&pending,&dev,47));
  pending.last_token=1;pending.phase=WR_REF_CLOSING;
  assert(!wr_iot_registry_after_unregister(&pending,&dev,47,0));
  assert(wr_iot_registry_after_unregister(&pending,&dev,47,1));
  assert(pending.removal_stage==1&&pending.device==&dev);
  assert(!wr_iot_registry_after_unregister(&pending,&dev,47,1));
  assert(!wr_iot_registry_finish_after_unregister(&pending,&dev,47,1,1,1));
  pending.phase=WR_REF_IDLE;pending.close_stage=4;
  assert(!wr_iot_registry_finish_after_unregister(&pending,&dev,48,1,1,1));
  assert(!wr_iot_registry_finish_after_unregister(&pending,&dev,47,0,1,1));
  assert(!wr_iot_registry_finish_after_unregister(&pending,&dev,47,1,0,1));
  assert(!wr_iot_registry_finish_after_unregister(&pending,&dev,47,1,1,0));
  assert(pending.removal_stage==1&&pending.device==&dev);
  assert(wr_iot_registry_finish_after_unregister(&pending,&dev,47,1,1,1));
  assert(!pending.device&&!pending.published);
  assert(!wr_iot_registry_finish_after_unregister(&pending,&dev,47,1,1,1));
 }
 {struct wr_iot_interface_ref family[3]={0};int dev[3]={0};
  for(int i=0;i<3;i++){
   wr_iot_ref_init(&family[i],&dev[i],(unsigned long)(i+1));
   family[i].published=1;
   assert(wr_iot_ref_reserve(&family[i],&dev[i],(unsigned long)(i+1),1));
   assert(!wr_iot_registry_count_matches(family,3,(unsigned int)i));
   assert(wr_iot_ref_open_finish(&family[i],&dev[i],(unsigned long)(i+1),1,1));
  }
  assert(wr_iot_registry_count_matches(family,3,3));
  assert(!wr_iot_registry_count_matches(family,3,2));
  assert(wr_iot_ref_begin_close(&family[2],&dev[2],3,1));
  assert(!wr_iot_registry_count_matches(family,3,3));
  assert(wr_iot_ref_consume(&family[2],&dev[2],3,1));
  assert(wr_iot_registry_count_matches(family,3,2));
  family[1].published=0;
  assert(!wr_iot_registry_count_matches(family,3,2));
  assert(!wr_iot_registry_count_matches(0,3,0));
 }
 return 0;
}
