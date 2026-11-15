/* Private implementation included ONLY by rc-runtime.c after its receipt.
 * Cleanup uses the same RC-owned receipt storage that preflight inspected. */
#ifndef WR_IOT_RADIO_ON_RELEASE_RUNTIME_H
#define WR_IOT_RADIO_ON_RELEASE_RUNTIME_H
#include "radio-on-release.h"
static struct wr_iot_on_restore *radio_on_releasing;
static void rc_on_release_wipe(void *data,size_t length)
{volatile unsigned char *p=data;while(length--)*p++=0;}
static void rc_on_release_cleanup(void *context)
{
 struct wr_iot_on_restore *s=context;struct wr_iot_on_admission *a=s->generation.admission;
 size_t i;
 for(i=0;i<a->profile.files.count;i++)if(a->profile.files.saved[i].data)
  rc_on_release_wipe(a->profile.files.saved[i].data,a->profile.files.saved[i].size);
 wr_iot_bundle_release(&a->profile.files);rc_on_release_wipe(&a->profile,sizeof(a->profile));
 rc_on_release_wipe(&s->generation.desired,sizeof(s->generation.desired));
 radio_off_receipt_valid=0;rc_on_release_wipe(&radio_off_receipt,sizeof(radio_off_receipt));
 s->generation.phase=WR_ON_GEN_COMMITTED;s->generation.admission=NULL;
 s->main.generation=NULL;s->guest.main=NULL;s->services.guest=NULL;
 s->multicast.main=NULL;s->multicast.guest=NULL;
 a->phase=WR_ON_ADMISSION_RELEASED;a->busy=0;
 wr_iot_rc_shutdown.radio_off_owned=0;s->phase=WR_ON_RESTORE_RELEASED;s->busy=0;radio_on_releasing=NULL;
 wr_iot_service_guard_leave(a->guard);a->guard=0;
}
int wr_iot_rc_radio_on_release(struct wr_iot_on_restore *s)
{
 struct wr_iot_on_admission *a;unsigned char expected[64],current[64];
 if(!s||s->owner!=getpid()||s->busy||!s->generation.admission)return 0;
 a=s->generation.admission;
 if(s->phase==WR_ON_RESTORE_RELEASING){
  if(radio_on_releasing!=s||a->owner!=getpid()||a->guard!=1||a->busy!=1||
     a->fence.owner!=getpid()||a->fence.level!=1||a->phase!=WR_ON_ADMISSION_CAPTURED||
     !a->profile.active||!radio_off_receipt_valid||!wr_iot_rc_shutdown.radio_off_owned||
     !wr_iot_physical_stop_request_encode(expected,sizeof(expected),&a->released)||
     !wr_iot_physical_stop_request_encode(current,sizeof(current),&radio_off_receipt)||
     memcmp(expected,current,sizeof(current))||!wr_iot_rc_shutdown.active)return 0;
 }else{
  if(s->phase!=WR_ON_RESTORE_HANDOFF||radio_on_releasing||!radio_off_receipt_valid)return 0;
  if(!s->wan.owner&&!wr_iot_wan_followup_capture(&s->wan,1))return 0;
  if(!wr_iot_on_release_current(s)||
     !wr_iot_physical_stop_request_encode(expected,sizeof(expected),&a->released)||
     !wr_iot_physical_stop_request_encode(current,sizeof(current),&radio_off_receipt)||
     memcmp(expected,current,sizeof(current)))return 0;
  radio_on_releasing=s;s->phase=WR_ON_RESTORE_RELEASING;
 }
 s->busy=1;
 if(!wr_iot_radio_stop_fence_end_cleanup(&a->fence,rc_on_release_cleanup,s)){s->busy=0;return 0;}
 return s->phase==WR_ON_RESTORE_RELEASED;
}
#endif
