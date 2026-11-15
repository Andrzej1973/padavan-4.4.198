#define _GNU_SOURCE
#include <unistd.h>
#include "radio-on-shutdown-check.h"
#include "rc-quiesce.h"
#include "rc-backend.h"
#include "rc-shutdown-admission.h"
int wr_iot_on_shutdown_closed_current(struct wr_iot_on_restore *s,const struct wr_iot_rc_quiesce *off)
{
 static const char hex[]="0123456789abcdef";
 struct wr_iot_control_result on={0};struct wr_iot_driver_closed_result closed={0};
 unsigned i;int state;
 if(!s||s->owner!=getpid()||s->busy||s->phase!=WR_ON_RESTORE_HANDOFF||
    !s->handoff_created||!wr_iot_rc_shutdown.active||
    (wr_iot_rc_shutdown.pending!=SIGTERM
#ifdef SIGQUIT
     &&wr_iot_rc_shutdown.pending!=SIGQUIT
#endif
    )||s->main.owner!=getpid()||s->main.generation!=&s->generation||
    !s->generation.admission||!s->generation.main_may_have_started||!s->generation.admission->profile.active||
    !wr_iot_on_generation_origin_current(&s->generation)||
    s->guest.owner!=getpid()||s->guest.busy||s->guest.main!=&s->main||
    (s->guest.desired!=0&&s->guest.desired!=1)||
    s->guest.phase!=(s->guest.desired?WR_ON_GUEST_DOWN_OBSERVED:WR_ON_GUEST_POLICY_OFF)||
    !wr_iot_restart_guest_admin_state(&state)||state)return 0;
 for(i=0;i<16;i++){on.id[2*i]=hex[s->open_id[i]>>4];on.id[2*i+1]=hex[s->open_id[i]&15];}
 on.created=s->handoff_created;on.state=WR_IOT_RESULT_APPLIED;
 if(off){
  if(!wr_iot_rc_rebind_shutdown_closed(&on,&s->generation.admission->released,&s->main.identity,off,&closed))return 0;
 }else if(!wr_iot_rc_rebind_preopen_rejected(&on,&s->generation.admission->released,&s->main.identity))return 0;
 /* Normal OFF has already validated/committed its CURRENT profile. Do not
  * compare or restore the obsolete startup profile after this owned change. */
 return wr_iot_on_generation_origin_current(&s->generation)&&
  wr_iot_restart_guest_admin_state(&state)&&!state;
}

int wr_iot_on_shutdown_rejected_current(struct wr_iot_on_restore *s)
{
 static const char hex[]="0123456789abcdef";struct wr_iot_control_result on={0};unsigned i;
 if(!s||s->owner!=getpid()||s->busy||s->phase!=WR_ON_RESTORE_HANDOFF||!s->handoff_created||
    s->main.owner!=getpid()||s->main.generation!=&s->generation||
    !s->generation.admission||!s->generation.admission->profile.active||!wr_iot_on_generation_origin_current(&s->generation))return 0;
 for(i=0;i<16;i++){on.id[2*i]=hex[s->open_id[i]>>4];on.id[2*i+1]=hex[s->open_id[i]&15];}
 on.created=s->handoff_created;on.state=WR_IOT_RESULT_APPLIED;
 return wr_iot_rc_rebind_preopen_rejected(&on,&s->generation.admission->released,&s->main.identity)&&
  wr_iot_on_generation_origin_current(&s->generation);
}
