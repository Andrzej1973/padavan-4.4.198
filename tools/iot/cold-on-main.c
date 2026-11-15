#define _GNU_SOURCE
#include <unistd.h>
#include "cold-on-main.h"
#include "rc-backend.h"
#include "rc-runtime.h"
#include "rc-shutdown-admission.h"
static int cold_main_origin(struct wr_iot_cold_generation *g)
{
 struct wr_iot_cold_admission *a=g->admission;
 struct wr_iot_physical_stop_request historical={0};struct wr_iot_rc_mode mode={0};
 return a&&a->down.epoch&&a->down.generation&&a->down.main_close_serial&&a->owner==getpid()&&a->busy==1&&a->guard==1&&a->phase==WR_COLD_CAPTURED&&
  a->fence.owner==getpid()&&a->fence.level==1&&wr_iot_rc_shutdown.active&&
  !wr_iot_rc_shutdown.pending&&wr_iot_rc_shutdown.radio_off_owned&&
  wr_iot_radio_profile_owned(&a->profile)&&a->profile.files.count==1&&
  !a->profile.recovering&&!a->profile.removing&&
  !wr_iot_rc_radio_off_receipt(&historical)&&
  wr_iot_rc_radio_on_mode_read(&mode)&&mode.router==1&&mode.radio==1&&mode.mode==0&&
  wr_iot_generated_matches(&a->profile.files.generated[0],a->profile.files.paths[0])&&
  wr_iot_cold_generation_profile_current(g);
}
int wr_iot_cold_main_begin(struct wr_iot_cold_main *s,struct wr_iot_cold_generation *g)
{
 enum wr_iot_restart_up_result result;
 if(!s||!g||s->owner||s->busy||s->generation||s->phase!=WR_COLD_MAIN_IDLE||
    g->owner!=getpid()||g->busy||g->main_may_have_started||g->phase!=WR_COLD_GEN_VERIFIED||
    wr_iot_cold_generation_step(g)!=1)return 0;
 s->owner=getpid();s->busy=1;s->generation=g;s->phase=WR_COLD_MAIN_WAIT;
 g->main_may_have_started=1;
 result=wr_iot_restart_main_up();
 if(result==WR_RESTART_UP_NOT_SUBMITTED)s->phase=WR_COLD_MAIN_NOT_SUBMITTED;
 s->busy=0;return result==WR_RESTART_UP_RETURNED;
}
int wr_iot_cold_main_step(struct wr_iot_cold_main *s)
{
 struct wr_iot_idle_result before={0},after={0};struct wr_iot_cold_generation *g;int ok=0;
 if(!s||s->owner!=getpid()||s->busy||!s->generation||
    (s->phase!=WR_COLD_MAIN_WAIT&&s->phase!=WR_COLD_MAIN_READY))return 0;
 g=s->generation;
 if(g->owner!=getpid()||g->busy||!g->main_may_have_started||g->phase!=WR_COLD_GEN_VERIFIED)return 0;
 s->busy=1;
 if(cold_main_origin(g)&&wr_iot_driver_initial_idle_read(g->admission->nonce,&before)&&
    cold_main_origin(g)&&wr_iot_driver_initial_idle_read(g->admission->nonce,&after)&&
    before.epoch>g->admission->down.epoch&&before.generation==g->admission->down.generation&&
    before.serial&&after.serial>before.serial&&before.epoch==after.epoch&&
    before.generation==after.generation&&
    (!s->identity.adapter_epoch||(s->identity.adapter_epoch==after.epoch&&
     s->identity.device_generation==after.generation))&&cold_main_origin(g)){
  s->identity.adapter_epoch=after.epoch;s->identity.device_generation=after.generation;
  s->phase=WR_COLD_MAIN_READY;ok=1;
 }
 s->busy=0;return ok;
}
