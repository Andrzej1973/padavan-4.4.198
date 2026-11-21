#define _GNU_SOURCE
#include <unistd.h>
#include "restart-restore.h"
#include "rc-quiesce.h"
#include "rc-backend.h"
#include "rc-shutdown-admission.h"
#include "restart-initial-handoff.h"
#include <string.h>
static int initial_cancel_current(struct wr_iot_restart_restore *s,const struct wr_iot_rc_quiesce *off,int preopen_only)
{
 static const char hex[]="0123456789abcdef";
 struct wr_iot_control_request r={0};unsigned i;int ok;
 if(s->initial_start_claimed!=0&&s->initial_start_claimed!=1)return 0;
 for(i=0;i<16;i++){r.id[2*i]=hex[s->open_id[i]>>4];r.id[2*i+1]=hex[s->open_id[i]&15];}
 r.created=s->handoff_created;r.request=s->generation.origin.desired;s->busy=1;
 if(!s->initial_start_claimed)ok=!off&&wr_iot_rc_initial_restart_unclaimed_current(s,&r);
 else if(off){struct wr_iot_driver_closed_result closed={0};ok=wr_iot_rc_initial_restart_shutdown_closed(s,&r,off,&closed);}
 else ok=wr_iot_rc_initial_restart_preopen_rejected(s,&r)||(!preopen_only&&(wr_iot_rc_initial_restart_rollback_closed(s,&r)||wr_iot_rc_initial_restart_committed_closed(s,&r)));
 {volatile unsigned char *p=(volatile unsigned char*)&r;size_t n=sizeof(r);while(n--)*p++=0;}
 s->busy=0;return ok;
}
int wr_iot_restart_restore_cancel_check(struct wr_iot_restart_restore *s,const struct wr_iot_rc_quiesce *off)
{
 static const char hex[]="0123456789abcdef";
 struct wr_iot_control_result on={0};struct wr_iot_driver_closed_result closed={0};
 unsigned i;int state;
 if(!s||s->owner!=getpid()||s->busy||s->phase!=WR_RESTORE_HANDOFF||
    !s->handoff_created||!wr_iot_rc_shutdown.active||
    (wr_iot_rc_shutdown.pending!=SIGTERM
#ifdef SIGQUIT
     &&wr_iot_rc_shutdown.pending!=SIGQUIT
#endif
    )||s->main.owner!=getpid()||s->main.generation!=&s->generation||
    !s->generation.main_may_have_started||!s->generation.profile.active||
    !wr_iot_restart_generation_origin_current(&s->generation)||
    s->guest.owner!=getpid()||s->guest.busy||s->guest.main!=&s->main||
    (s->guest.desired!=0&&s->guest.desired!=1)||
    s->guest.phase!=(s->guest.desired?WR_GUEST_DOWN_OBSERVED:WR_GUEST_POLICY_OFF)||
    !wr_iot_restart_guest_admin_state(&state)||state)return 0;
 for(i=0;i<16;i++){on.id[2*i]=hex[s->open_id[i]>>4];on.id[2*i+1]=hex[s->open_id[i]&15];}
 on.created=s->handoff_created;on.state=WR_IOT_RESULT_APPLIED;
 if(s->generation.origin.origin==WR_PHYSICAL_ORIGIN_INITIAL){
  /* Current normal CLOSED is distinct from original INITIAL RELEASE. */
  if(!initial_cancel_current(s,off,0))return 0;
 }else if(off){
  if(!wr_iot_rc_rebind_shutdown_closed(&on,&s->generation.origin.physical,&s->main.identity,off,&closed))return 0;
 }else if(!wr_iot_rc_rebind_preopen_rejected(&on,&s->generation.origin.physical,&s->main.identity))return 0;
 /* Normal OFF has already validated/committed its CURRENT profile. Do not
  * compare or restore the obsolete startup profile after this owned change. */
 return wr_iot_restart_generation_origin_current(&s->generation)&&
  wr_iot_restart_guest_admin_state(&state)&&!state;
}

int wr_iot_restart_restore_preopen_rejected(struct wr_iot_restart_restore *s)
{
 static const char hex[]="0123456789abcdef";struct wr_iot_control_result on={0};unsigned i;
 if(!s||s->owner!=getpid()||s->busy||s->phase!=WR_RESTORE_HANDOFF||!s->handoff_created||
    s->main.owner!=getpid()||s->main.generation!=&s->generation||
    !s->generation.profile.active||!wr_iot_restart_generation_origin_current(&s->generation))return 0;
 for(i=0;i<16;i++){on.id[2*i]=hex[s->open_id[i]>>4];on.id[2*i+1]=hex[s->open_id[i]&15];}
 on.created=s->handoff_created;on.state=WR_IOT_RESULT_APPLIED;
 return (s->generation.origin.origin==WR_PHYSICAL_ORIGIN_INITIAL?
  initial_cancel_current(s,NULL,1):wr_iot_rc_rebind_preopen_rejected(&on,&s->generation.origin.physical,&s->main.identity))&&
  wr_iot_restart_generation_origin_current(&s->generation);
}
