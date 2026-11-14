#define _GNU_SOURCE
#include <string.h>
#include <unistd.h>
#include "restart-main-controller.h"
#include "restart-profile.h"
#include "rc-shutdown-admission.h"
int wr_iot_restart_main_begin(struct wr_iot_restart_main *s,
 struct wr_iot_restart_generation *g,const unsigned char *id)
{
 unsigned i,nonzero=0;enum wr_iot_restart_up_result result;
 if(!s||!g||!id||s->owner||s->busy||s->phase!=WR_MAIN_IDLE||
    g->owner!=getpid()||g->busy||g->main_may_have_started||
    g->phase!=WR_RESTART_GEN_VERIFIED||!g->profile.active||
    !wr_iot_rc_shutdown.active||wr_iot_rc_shutdown.pending)return 0;
 for(i=0;i<16;i++)nonzero|=id[i];
 if(!nonzero||!wr_iot_restart_generation_step(g))return 0;
 s->owner=getpid();s->busy=1;s->generation=g;memcpy(s->open_id,id,16);
 /* Block restoration BEFORE the call. Even an error may follow ndo_open. */
 g->main_may_have_started=1;s->phase=WR_MAIN_WAIT;
 result=wr_iot_restart_main_up();
 if(result==WR_RESTART_UP_NOT_SUBMITTED){
  /* Existing foreign UP is possible; conservatively keep restoration fenced.
   * Recovery must inspect it, never retry UP or restore solely from this code. */
  s->phase=WR_MAIN_NOT_SUBMITTED;
 }
 s->busy=0;return result==WR_RESTART_UP_RETURNED;
}
int wr_iot_restart_main_step(struct wr_iot_restart_main *s)
{
 struct wr_iot_driver_identity current={0};int ok=0;
 if(!s||s->owner!=getpid()||s->busy||!s->generation||
    (s->phase!=WR_MAIN_WAIT&&s->phase!=WR_MAIN_READY)||
    s->generation->owner!=getpid()||s->generation->busy||
    !s->generation->main_may_have_started||!s->generation->profile.active||
    s->generation->phase!=WR_RESTART_GEN_VERIFIED||!wr_iot_rc_shutdown.active||
    wr_iot_rc_shutdown.pending||!wr_iot_radio_profile_guard())return 0;
 s->busy=1;
 if(wr_iot_restart_generation_origin_current(s->generation)&&
    wr_iot_generated_matches(&s->generation->profile.files.generated[0],s->generation->profile.files.paths[0])&&
    wr_iot_restart_profile_current(&s->generation->origin.desired)&&
    wr_iot_rebind_configuration_current(&s->generation->origin.physical,s->open_id,&current)&&
    current.adapter_epoch>s->generation->origin.physical.epoch&&
    current.device_generation==s->generation->origin.physical.generation&&
    (!s->identity.adapter_epoch||
     (current.adapter_epoch==s->identity.adapter_epoch&&current.device_generation==s->identity.device_generation))&&
    wr_iot_restart_generation_origin_current(s->generation)&&!wr_iot_rc_shutdown.pending){s->identity=current;s->phase=WR_MAIN_READY;ok=1;}
 s->busy=0;return ok;
}
