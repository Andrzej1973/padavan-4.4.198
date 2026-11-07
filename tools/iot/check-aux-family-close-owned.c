#include "aux-close-claim.h"
#include "aux-family-close.h"
#include "radio-transition.h"
#include <assert.h>
#include <string.h>
#define WDEV_NUM_MAX 1
#define EBUSY 16
#define NDIS_STATUS_SUCCESS 0
#define NDIS_STATUS_FAILURE 1
typedef int INT;typedef unsigned long ULONG;typedef void *PNET_DEV;
typedef struct {
 int wr_iot_transition_lock,wr_iot_ticket_wait;unsigned int count;
 void *net_dev;
 struct wr_iot_interface_ref wr_iot_interface_refs[2];
 struct wr_iot_family_close wr_iot_family_close[2];
 struct wr_iot_radio_transition wr_iot_transition;
} RTMP_ADAPTER;
static int held,family_result,down_result,family_calls,down_calls,pins,hnat,wakes,reset_in_family,reset_in_hnat;
static RTMP_ADAPTER *test_ad;
#define RTMP_IRQ_LOCK(l,f) do{(void)(l);(f)=0;assert(!held);held=1;}while(0)
#define RTMP_IRQ_UNLOCK(l,f) do{(void)(l);(void)(f);assert(held);held=0;}while(0)
#define VIRTUAL_IF_NUM(ad) ((ad)->count)
#define RT_MOD_HNAT_DEREG(dev) do{assert(dev&&!held);hnat++;if(reset_in_hnat)test_ad->wr_iot_transition.epoch++;}while(0)
#define RT_MOD_DEC_USE_COUNT() do{assert(!held&&pins==1);pins--;}while(0)
#define wake_up_all(q) do{(void)(q);assert(!held);wakes++;}while(0)
static int family_close(RTMP_ADAPTER *ad,PNET_DEV dev){
 assert(!held&&dev&&ad->wr_iot_interface_refs[1].phase==WR_REF_CLOSING);
 assert(ad->wr_iot_family_close[1].phase==WR_FAMILY_CLOSE_IN_FLIGHT);
 family_calls++;if(reset_in_family)ad->wr_iot_transition.epoch++;return family_result;
}
static int wr_iot_virtual_down_checked(RTMP_ADAPTER *ad,const struct wr_iot_radio_ticket *t){
 assert(!held&&t&&ad->wr_iot_family_close[1].phase==WR_FAMILY_DOWN_IN_FLIGHT);
 down_calls++;if(down_result)return 1;
 ad->count--;ad->wr_iot_transition.virtual_down_stage=2;return 0;
}
#include "aux-family-close-owned.inc"
static void ready(RTMP_ADAPTER *ad,enum wr_iot_ref_family f,int *devices){
 memset(ad,0,sizeof *ad);test_ad=ad;wr_iot_radio_transition_init(&ad->wr_iot_transition);
 ad->wr_iot_transition.phase=WR_RADIO_READY;ad->wr_iot_transition.main_ready=1;ad->count=2;
 for(int i=0;i<2;i++){
  wr_iot_ref_init(&ad->wr_iot_interface_refs[i],&devices[i],i+1);
  ad->wr_iot_interface_refs[i].published=1;ad->wr_iot_interface_refs[i].last_token=i+1;
  ad->wr_iot_interface_refs[i].phase=WR_REF_OWNED;
  wr_iot_family_close_init(&ad->wr_iot_family_close[i]);
 }
 ad->wr_iot_interface_refs[0].family=WR_REF_FAMILY_MAIN;
 ad->wr_iot_interface_refs[1].family=f;ad->wr_iot_interface_refs[1].removing=1;
 family_calls=down_calls=hnat=wakes=reset_in_family=reset_in_hnat=0;pins=1;
}
int main(void){RTMP_ADAPTER ad;int dev[2];
 for(int k=0;k<2;k++){
  enum wr_iot_ref_family f=k?WR_REF_FAMILY_MONITOR:WR_REF_FAMILY_APCLI;
  ready(&ad,f,dev);ad.count=1;family_result=0;down_result=0;
  assert(wr_iot_aux_family_close_owned(&ad,&dev[1],f,family_close)==-EBUSY);
  assert(!family_calls&&!down_calls&&pins==1&&!ad.wr_iot_transition.busy);
  ready(&ad,f,dev);family_result=1;down_result=0;
  assert(wr_iot_aux_family_close_owned(&ad,&dev[1],f,family_close)==-EBUSY);
  assert(family_calls==1&&!down_calls&&!hnat&&pins==1);
  assert(ad.wr_iot_family_close[1].phase==WR_FAMILY_CLOSE_UNCERTAIN);
  assert(wr_iot_aux_family_close_owned(&ad,&dev[1],f,family_close)==-EBUSY&&family_calls==1);
  ready(&ad,f,dev);family_result=0;down_result=0;reset_in_family=1;
  assert(wr_iot_aux_family_close_owned(&ad,&dev[1],f,family_close)==-EBUSY);
  assert(family_calls==1&&!down_calls&&!hnat&&pins==1&&ad.count==2);
  assert(ad.wr_iot_family_close[1].phase==WR_FAMILY_CLOSE_UNCERTAIN);
#ifdef CONFIG_RA_HW_NAT_WIFI_NEW_ARCH
  ready(&ad,f,dev);family_result=0;down_result=0;reset_in_hnat=1;
  assert(wr_iot_aux_family_close_owned(&ad,&dev[1],f,family_close)==-EBUSY);
  assert(family_calls==1&&down_calls==1&&hnat==1&&pins==1&&ad.count==2);
  assert(ad.wr_iot_family_close[1].phase==WR_FAMILY_CLOSE_UNCERTAIN);
#endif
  ready(&ad,f,dev);family_result=0;down_result=1;
  assert(wr_iot_aux_family_close_owned(&ad,&dev[1],f,family_close)==-EBUSY);
  assert(family_calls==1&&down_calls==1&&pins==1);
  assert(ad.wr_iot_family_close[1].phase==WR_FAMILY_DOWN_RETRY);
  assert(wr_iot_aux_family_close_owned(&ad,&dev[1],f,family_close)==-EBUSY&&family_calls==1);
  ready(&ad,f,dev);down_result=0;
  assert(wr_iot_aux_family_close_owned(&ad,&dev[1],f,family_close)==0);
  assert(family_calls==1&&down_calls==1&&!pins&&wakes==1&&ad.count==1);
  assert(ad.wr_iot_family_close[1].phase==WR_FAMILY_CLOSE_DONE);
  assert(ad.wr_iot_interface_refs[1].phase==WR_REF_IDLE);
 }
 assert(!held);return 0;
}
