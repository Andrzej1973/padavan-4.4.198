#define _GNU_SOURCE
#include <string.h>
#include <unistd.h>
#include "cold-on-admission.h"
#include "rc-backend.h"
#include "rc-runtime.h"
#include "rc-shutdown-admission.h"
static int cold_origin(struct wr_iot_cold_admission *s)
{
 struct wr_iot_physical_stop_request historical={0};struct wr_iot_rc_mode mode={0};
 return !wr_iot_rc_radio_off_receipt(&historical)&&
  wr_iot_rc_radio_on_mode_read(&mode)&&mode.router==1&&mode.radio==1&&mode.mode==0&&
  wr_iot_initial_down_current(s->nonce,&s->down);
}
int wr_iot_cold_admission_current(struct wr_iot_cold_admission *s)
{
 return s&&s->owner==getpid()&&!s->busy&&s->guard==1&&s->phase==WR_COLD_CAPTURED&&
  s->fence.owner==getpid()&&s->fence.level==1&&wr_iot_rc_shutdown.active&&
  !wr_iot_rc_shutdown.pending&&wr_iot_rc_shutdown.radio_off_owned&&
  wr_iot_radio_profile_owned(&s->profile)&&s->profile.files.count==1&&
  !s->profile.generated&&!s->profile.recovering&&!s->profile.removing&&
  !s->profile.files.journalled&&!s->profile.files.dirty&&!s->profile.files.pending&&
  cold_origin(s)&&wr_iot_generated_matches(&s->profile.files.generated[0],s->profile.files.paths[0])&&
  cold_origin(s);
}
int wr_iot_cold_admission_begin(struct wr_iot_cold_admission *s,const unsigned char *nonce)
{
 struct wr_iot_physical_stop_request historical={0};struct wr_iot_rc_mode mode={0};
 unsigned i,nonzero=0;int guard;
 if(!s||!nonce||s->owner||s->busy||s->guard||s->phase!=WR_COLD_IDLE||s->profile.active||
    s->profile.files.count||s->fence.owner||s->fence.level||wr_iot_rc_shutdown.active||
    wr_iot_rc_shutdown.pending||wr_iot_rc_shutdown.radio_off_owned||wr_iot_rc_shutdown.radio_on_owned)return 0;
 for(i=0;i<16;i++)nonzero|=nonce[i];
 if(!nonzero)return 0;
 s->busy=1;guard=wr_iot_service_guard_enter(1);
 if(guard!=1){s->busy=0;return 0;}
 if(wr_iot_rc_radio_off_receipt(&historical)||!wr_iot_rc_radio_on_mode_read(&mode)||
    mode.router!=1||mode.radio!=1||mode.mode!=0||!wr_iot_radio_stop_fence_begin(&s->fence)){
  wr_iot_service_guard_leave(guard);s->busy=0;return 0;
 }
 s->owner=getpid();s->guard=guard;s->phase=WR_COLD_REFUSED;
 memcpy(s->nonce,nonce,16);wr_iot_rc_shutdown.radio_off_owned=1;
 if(wr_iot_initial_down_observe(s->nonce,&s->down)&&cold_origin(s)&&
    wr_iot_radio_profile_take(&s->profile)&&s->profile.files.saved[0].existed&&
    s->profile.files.saved[0].size&&s->profile.files.count==1&&
    wr_iot_generated_matches(&s->profile.files.generated[0],s->profile.files.paths[0])&&
    cold_origin(s)&&!wr_iot_rc_shutdown.pending)s->phase=WR_COLD_CAPTURED;
 s->busy=0;return 1;
}
static void cold_cancel_cleanup(void *context)
{
 struct wr_iot_cold_admission *s=context;volatile unsigned char *p;size_t n;
 wr_iot_bundle_release(&s->profile.files);
 p=(volatile unsigned char *)&s->profile;n=sizeof(s->profile);while(n--)*p++=0;
 memset(s->nonce,0,sizeof(s->nonce));memset(&s->down,0,sizeof(s->down));
 wr_iot_rc_shutdown.radio_off_owned=0;s->phase=WR_COLD_CANCELLED;s->busy=0;
 wr_iot_service_guard_leave(s->guard);s->guard=0;
}
int wr_iot_cold_admission_cancel(struct wr_iot_cold_admission *s)
{
 if(!s||s->owner!=getpid()||s->busy||s->guard!=1||s->fence.owner!=getpid()||s->fence.level!=1||
    !wr_iot_rc_shutdown.active||!wr_iot_rc_shutdown.radio_off_owned||
    (s->phase!=WR_COLD_CAPTURED&&s->phase!=WR_COLD_REFUSED)||
    (s->profile.active&&(s->profile.owner!=getpid()||s->profile.generated||s->profile.recovering||
     s->profile.removing||s->profile.files.journalled||s->profile.files.dirty||s->profile.files.pending)))return 0;
 s->busy=1;
 if(!wr_iot_radio_stop_fence_end_cleanup(&s->fence,cold_cancel_cleanup,s)){s->busy=0;return 0;}
 return s->phase==WR_COLD_CANCELLED;
}
