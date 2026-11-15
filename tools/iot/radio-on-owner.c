#define _GNU_SOURCE
#include <string.h>
#include <unistd.h>
#include "radio-on-owner.h"
#include "radio-on-release.h"
#include "radio-on-followup.h"
#include "rc-shutdown-admission.h"
#include "rc-runtime.h"
#include "radio-on-rollback-state.h"
#include "radio-off-observe.h"
#include "radio-on-shutdown.h"
#include "radio-on-disabled.h"
#include "precreated-entropy.h"
#include <time.h>
enum on_owner_phase {ON_OWNER_IDLE,ON_OWNER_ADMITTED,ON_OWNER_RESTORE,ON_OWNER_HANDOFF,ON_OWNER_REBIND,ON_OWNER_RELEASE,ON_OWNER_FOLLOWUP,ON_OWNER_DONE,ON_OWNER_RETAINED};
static struct {
 pid_t owner;int busy,reload,iot_enabled;enum on_owner_phase phase;
 struct wr_iot_control_request input;unsigned char nonce[16];
 struct wr_iot_on_shutdown shutdown;
 struct wr_iot_on_disabled disabled;
 struct wr_iot_on_admission admission;struct wr_iot_on_restore restore;
} on_owner;
static void on_owner_wipe(void *data,size_t size)
{volatile unsigned char*p=data;while(size--)*p++=0;}
int wr_iot_rc_radio_on_begin(const struct wr_iot_control_request *r,int reload)
{
 struct wr_iot_control_fields fields;struct wr_iot_request desired={0};unsigned char nonce[16]={0};unsigned i,nonzero=0;int owned=0;
 if(!r||(reload!=0&&reload!=1)||on_owner.owner||on_owner.busy||on_owner.phase!=ON_OWNER_IDLE||
    wr_iot_rc_shutdown.active||wr_iot_rc_shutdown.pending||wr_iot_rc_shutdown.radio_off_owned||
    wr_iot_rc_shutdown.radio_on_owned||(r->request.enabled!=0&&r->request.enabled!=1)||!r->created||
    !memchr(r->id,0,sizeof(r->id))||!wr_iot_control_id(r->id))return 0;
#define BOUNDED(f) if(!memchr(r->request.f,0,sizeof(r->request.f)))return 0;
 BOUNDED(ssid) BOUNDED(password) BOUNDED(gateway) BOUNDED(mask) BOUNDED(first) BOUNDED(last)
#undef BOUNDED
 for(i=0;i<16;i++){
  unsigned char a=r->id[2*i],b=r->id[2*i+1];
  nonce[i]=(unsigned char)(((a<='9'?a-'0':a-'a'+10)<<4)|(b<='9'?b-'0':b-'a'+10));nonzero|=nonce[i];
 }
 if(!nonzero)goto done;
 fields.values[0]="1";fields.values[1]=(char*)r->request.ssid;fields.values[2]=(char*)r->request.password;
 fields.values[3]=(char*)r->request.gateway;fields.values[4]=(char*)r->request.mask;
 fields.values[5]=(char*)r->request.first;fields.values[6]=(char*)r->request.last;
 if(r->request.enabled){
  if(!wr_iot_request_read(&desired,wr_iot_control_read,&fields,1,1,0,NULL,0))goto done;
 }else{
  /* Disabled intent carries no credentials or subnet to accidentally apply. */
  if(r->request.ssid[0]||r->request.password[0]||r->request.gateway[0]||
     r->request.mask[0]||r->request.first[0]||r->request.last[0])goto done;
 }
 on_owner.busy=1;
 if(!wr_iot_on_admission_begin_reload(&on_owner.admission,reload))goto done;
 on_owner.owner=getpid();on_owner.reload=reload;on_owner.iot_enabled=r->request.enabled;wr_iot_rc_shutdown.radio_on_owned=1;
 memcpy(on_owner.input.id,r->id,sizeof(r->id));on_owner.input.created=r->created;
 on_owner.input.request=desired;
 memcpy(on_owner.nonce,nonce,sizeof(nonce));
 on_owner.phase=on_owner.admission.phase==WR_ON_ADMISSION_CAPTURED?ON_OWNER_ADMITTED:ON_OWNER_RETAINED;
 owned=1;
 done:on_owner.busy=0;on_owner_wipe(nonce,sizeof(nonce));on_owner_wipe(&desired,sizeof(desired));return owned;
}
int wr_iot_radio_on_pending(void)
{return on_owner.owner!=0||wr_iot_rc_shutdown.radio_on_owned;}
static void on_cancelled_cleanup(void *unused)
{
 struct wr_iot_on_admission *a=&on_owner.admission;size_t i;int guard=a->guard;
 (void)unused;
 for(i=0;i<a->profile.files.count;i++)if(a->profile.files.saved[i].data)
  on_owner_wipe(a->profile.files.saved[i].data,a->profile.files.saved[i].size);
 wr_iot_bundle_release(&a->profile.files);
 on_owner_wipe(&on_owner,sizeof(on_owner));
 wr_iot_rc_shutdown.radio_off_owned=0;wr_iot_rc_shutdown.radio_on_owned=0;
 wr_iot_service_guard_leave(guard);
}
static int on_early_cancel_finish(void)
{
 struct wr_iot_on_admission *a=&on_owner.admission;
 struct wr_iot_physical_stop_request receipt={0};unsigned char before[64],after[64];
 struct wr_iot_on_restore *r=&on_owner.restore;
 int refused=on_owner.phase==ON_OWNER_RETAINED&&r->owner==getpid()&&
  !r->busy&&r->phase==WR_ON_RESTORE_RETAINED&&!r->generation.owner&&
  !r->generation.busy&&!r->generation.admission&&!r->generation.main_may_have_started&&
  !r->radio_state_attempted&&!r->rollback_state_attempted&&!r->main.owner&&
  !r->guest.owner&&!r->multicast.owner&&!r->services.owner&&!r->wan.owner&&
  !r->terminal.owner&&!r->child.owner&&!r->child.attempted&&!r->handoff_created;
 if(!((on_owner.phase==ON_OWNER_ADMITTED&&!r->owner)||refused)||
    a->owner!=getpid()||a->busy||a->guard!=1||a->phase!=WR_ON_ADMISSION_CAPTURED||
    a->fence.owner!=getpid()||a->fence.level!=1||!wr_iot_rc_shutdown.active||
    !wr_iot_radio_profile_owned(&a->profile)||a->profile.generated||a->profile.recovering||a->profile.removing||
    a->profile.files.count!=1||a->profile.files.journalled||a->profile.files.dirty||a->profile.files.pending||
    !wr_iot_generated_matches(&a->profile.files.generated[0],a->profile.files.paths[0])||
    !wr_iot_rc_radio_off_receipt(&receipt)||
    !wr_iot_physical_stop_request_encode(before,sizeof(before),&a->released)||
    !wr_iot_physical_stop_request_encode(after,sizeof(after),&receipt)||memcmp(before,after,sizeof(before))||
    !wr_iot_rc_radio_on_rollback_current(&a->released)||
    !wr_iot_radio_recovery_down_observed(&a->released))return 0;
 return wr_iot_radio_stop_fence_end_cleanup(&a->fence,on_cancelled_cleanup,NULL);
}
static int on_cancelled_finish(void)
{
 struct wr_iot_on_restore *r=&on_owner.restore;struct wr_iot_on_generation *g=&r->generation;
 struct wr_iot_on_admission *a=&on_owner.admission;struct wr_iot_physical_stop_request receipt={0};
 unsigned char before[64],after[64];
 if(g->owner!=getpid()||g->busy||g->main_may_have_started||g->phase!=WR_ON_GEN_RESTORED||
    g->admission!=a||r->main.owner||r->guest.owner||r->services.owner||r->multicast.owner||
    r->wan.owner||r->terminal.owner||r->child.owner||r->child.attempted||
    !r->rollback_state_attempted||a->owner!=getpid()||
    a->busy!=1||a->guard!=1||a->fence.owner!=getpid()||a->fence.level!=1||
    !wr_iot_rc_shutdown.active||!wr_iot_rc_shutdown.radio_off_owned||!wr_iot_rc_shutdown.radio_on_owned||
    !wr_iot_radio_profile_owned(&a->profile)||!a->profile.recovered||!a->profile.recovering||
    a->profile.files.count!=1||a->profile.files.pending||
    !wr_iot_generated_matches(&a->profile.restored_file,a->profile.files.paths[0])||
    !wr_iot_rc_radio_off_receipt(&receipt)||
    !wr_iot_physical_stop_request_encode(before,sizeof(before),&a->released)||
    !wr_iot_physical_stop_request_encode(after,sizeof(after),&receipt)||memcmp(before,after,sizeof(before))||
    !wr_iot_rc_radio_on_rollback_current(&a->released)||
    !wr_iot_radio_recovery_down_observed(&a->released))return 0;
 return wr_iot_radio_stop_fence_end_cleanup(&a->fence,on_cancelled_cleanup,NULL);
}
static void on_postup_root_cleanup(void *context)
{
 (void)context;on_owner_wipe(&on_owner,sizeof(on_owner));
 wr_iot_rc_shutdown.radio_on_owned=0;
}
static int on_shutdown_begin_fresh(void)
{
 static const char hex[]="0123456789abcdef";
 struct wr_iot_control_request off={0};unsigned char bytes[32]={0};struct timespec now;unsigned i;int admitted=0;
 if(clock_gettime(CLOCK_MONOTONIC,&now)||now.tv_sec<=0||
    (unsigned long long)now.tv_sec<on_owner.restore.handoff_created||
    wr_iot_precreated_entropy(NULL,bytes,sizeof(bytes))!=(int)sizeof(bytes))goto done;
 for(i=0;i<16;i++){off.id[2*i]=hex[bytes[i]>>4];off.id[2*i+1]=hex[bytes[i]&15];}
 off.created=(unsigned long long)now.tv_sec;
 admitted=wr_iot_on_shutdown_begin(&on_owner.shutdown,&on_owner.restore,&off);
 done:on_owner_wipe(bytes,sizeof(bytes));on_owner_wipe(&off,sizeof(off));return admitted;
}
int wr_iot_radio_on_step(void)
{
 struct wr_iot_control_request r={0};int result=0;sigset_t queued;
 if(on_owner.owner!=getpid()||on_owner.busy||!wr_iot_rc_shutdown.radio_on_owned)return 0;
 if(wr_iot_rc_shutdown.active&&!sigpending(&queued)){
  if(sigismember(&queued,SIGTERM)==1)(void)wr_iot_rc_shutdown_note(SIGTERM);
#ifdef SIGQUIT
  else if(sigismember(&queued,SIGQUIT)==1)(void)wr_iot_rc_shutdown_note(SIGQUIT);
#endif
 }
 on_owner.busy=1;
 if(on_owner.phase==ON_OWNER_RETAINED&&!on_owner.restore.generation.owner){
  if(on_early_cancel_finish())return -1;
  on_owner.busy=0;return 0;
 }
 if(wr_iot_rc_shutdown.pending&&on_owner.phase==ON_OWNER_ADMITTED){
  if(on_early_cancel_finish())return -1;
  on_owner.busy=0;return 0;
 }
 if(wr_iot_rc_shutdown.pending&&!on_owner.restore.generation.main_may_have_started&&
    on_owner.restore.generation.owner==getpid()){
  (void)wr_iot_on_restore_step(&on_owner.restore);
  if(on_cancelled_finish())return -1;
  on_owner.busy=0;return 0;
 }
 if(!wr_iot_rc_shutdown.pending&&on_owner.restore.generation.owner==getpid()&&
    !on_owner.restore.generation.main_may_have_started&&
    (on_owner.phase==ON_OWNER_RETAINED||on_owner.restore.generation.phase==WR_ON_GEN_RESTORING||
     on_owner.restore.generation.phase==WR_ON_GEN_RESTORED)){
  if(wr_iot_on_restore_preup_recover(&on_owner.restore)==-1&&on_cancelled_finish())return -1;
  on_owner.busy=0;return 0;
 }
 if(wr_iot_rc_shutdown.pending&&on_owner.restore.generation.main_may_have_started&&
    !on_owner.restore.handoff_created&&on_owner.restore.generation.admission){
  (void)wr_iot_on_restore_step(&on_owner.restore);
  if(wr_iot_rc_radio_on_shutdown_release(&on_owner.restore,on_postup_root_cleanup,NULL))return -1;
  on_owner.busy=0;return 0;
 }
 if(wr_iot_rc_shutdown.pending&&on_owner.restore.handoff_created&&on_owner.restore.generation.admission){
  if(!on_owner.shutdown.owner){(void)on_shutdown_begin_fresh();on_owner.busy=0;return 0;}
  if(wr_iot_on_shutdown_step(&on_owner.shutdown)&&
     wr_iot_rc_radio_on_shutdown_closed_release(&on_owner.restore,
      on_owner.shutdown.phase==WR_ON_STOP_CLOSED?&on_owner.shutdown.off:NULL,on_postup_root_cleanup,NULL))return -1;
  on_owner.busy=0;return 0;
 }
 switch(on_owner.phase){
 case ON_OWNER_ADMITTED:
  on_owner.phase=ON_OWNER_RETAINED;
  if(wr_iot_on_restore_begin(&on_owner.restore,&on_owner.admission,&on_owner.input.request,on_owner.reload,on_owner.nonce))on_owner.phase=ON_OWNER_RESTORE;
  on_owner_wipe(&on_owner.input.request,sizeof(on_owner.input.request));
  break;
 case ON_OWNER_RESTORE:
  if(wr_iot_on_restore_step(&on_owner.restore))on_owner.phase=ON_OWNER_HANDOFF;
  else if(on_owner.restore.phase==WR_ON_RESTORE_RETAINED)on_owner.phase=ON_OWNER_RETAINED;
  break;
 case ON_OWNER_HANDOFF:
  if(!on_owner.iot_enabled){
   if(on_owner.disabled.owner?wr_iot_on_disabled_current(&on_owner.disabled):
      wr_iot_on_disabled_begin(&on_owner.disabled,&on_owner.restore,&on_owner.input))on_owner.phase=ON_OWNER_RELEASE;
   break;
  }
  r=on_owner.input;r.request=on_owner.restore.generation.desired;
  (void)wr_iot_on_restore_handoff(&on_owner.restore,&r);
  on_owner.phase=on_owner.restore.phase==WR_ON_RESTORE_HANDOFF?ON_OWNER_REBIND:ON_OWNER_RETAINED;
  break;
 case ON_OWNER_REBIND:
  if(wr_iot_on_rebind_step(&on_owner.restore))on_owner.phase=ON_OWNER_RELEASE;
  break;
 case ON_OWNER_RELEASE:
  if(on_owner.iot_enabled?wr_iot_rc_radio_on_release(&on_owner.restore):wr_iot_on_disabled_release(&on_owner.disabled))on_owner.phase=ON_OWNER_FOLLOWUP;
  break;
 case ON_OWNER_FOLLOWUP:
  if(on_owner.iot_enabled?wr_iot_on_followup_step(&on_owner.restore):wr_iot_on_disabled_followup(&on_owner.disabled)){on_owner.phase=ON_OWNER_DONE;result=1;}
  else if(on_owner.restore.phase==WR_ON_RESTORE_RETAINED)on_owner.phase=ON_OWNER_RETAINED;
  break;
 case ON_OWNER_DONE:result=1;break;
 default:break;
 }
 on_owner_wipe(&r,sizeof(r));on_owner.busy=0;return result;
}
int wr_iot_radio_on_retire(void)
{
 struct wr_iot_on_restore *r=&on_owner.restore;struct wr_iot_on_admission *a=&on_owner.admission;struct wr_iot_physical_stop_request receipt={0};size_t i;
 if(on_owner.owner!=getpid()||on_owner.busy||on_owner.phase!=ON_OWNER_DONE||on_owner.shutdown.owner||on_owner.shutdown.busy||
    !wr_iot_rc_shutdown.radio_on_owned||wr_iot_rc_shutdown.active||wr_iot_rc_shutdown.pending||wr_iot_rc_shutdown.radio_off_owned||
    a->owner!=getpid()||a->phase!=WR_ON_ADMISSION_RELEASED||a->busy||a->guard||a->fence.owner||a->fence.level||a->profile.active||a->profile.files.count||
    r->owner!=getpid()||r->phase!=WR_ON_RESTORE_DONE||r->busy||r->generation.owner!=getpid()||!r->generation.main_may_have_started||r->generation.phase!=WR_ON_GEN_COMMITTED||r->generation.busy||r->generation.admission||
    r->main.busy||r->main.generation||r->guest.busy||r->guest.main||r->services.busy||r->services.guest||
    r->multicast.busy||r->multicast.main||r->multicast.guest||r->wan.owner!=getpid()||r->wan.radio_on!=1||!r->wan.attempted||!r->wan.returned||
    !r->led_attempted||!r->led_returned||r->terminal.busy||r->terminal.guard||r->terminal.child||
    r->terminal.owner!=getpid()||!r->terminal.attempted||r->terminal.fence.owner||r->terminal.fence.level||r->terminal.result!=1||
    !wr_iot_iapp_child_closed(&r->child)||r->child.result!=1)return 0;
 if((on_owner.iot_enabled?r->handoff_created!=on_owner.input.created:
    (r->handoff_created||on_owner.disabled.owner!=getpid()||on_owner.disabled.restore!=r||on_owner.disabled.busy))||
    memcmp(r->open_id,on_owner.nonce,16)||wr_iot_rc_radio_off_receipt(&receipt))return 0;
 for(i=0;i<sizeof(on_owner.input.request);i++)if(((unsigned char*)&on_owner.input.request)[i])return 0;
 for(i=0;i<sizeof(r->generation.desired);i++)if(((unsigned char*)&r->generation.desired)[i])return 0;
 for(i=0;i<WR_IOT_BUNDLE_MAX;i++)if(a->profile.files.saved[i].data)return 0;
 on_owner.busy=1;
 if(!(on_owner.iot_enabled?wr_iot_on_followup_step(r):wr_iot_on_disabled_followup(&on_owner.disabled))){on_owner.busy=0;return 0;}
 on_owner_wipe(&on_owner,sizeof(on_owner));wr_iot_rc_shutdown.radio_on_owned=0;return 1;
}
