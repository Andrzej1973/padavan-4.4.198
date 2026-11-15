#define _GNU_SOURCE
#include <string.h>
#include <unistd.h>
#include "radio-on-main.h"
#include "restart-main-bridge.h"
#include "rc-shutdown-admission.h"
int wr_iot_on_main_begin(struct wr_iot_on_main *s,struct wr_iot_on_generation *g,const unsigned char *id)
{
 unsigned i,nonzero=0;enum wr_iot_restart_up_result result;
 if(!s||!g||!id||s->owner||s->busy||s->generation||s->phase!=WR_ON_MAIN_IDLE||
    g->owner!=getpid()||g->busy||g->main_may_have_started||g->phase!=WR_ON_GEN_VERIFIED||
    !wr_iot_rc_shutdown.active||wr_iot_rc_shutdown.pending)return 0;
 for(i=0;i<16;i++)nonzero|=id[i];
 if(!nonzero||wr_iot_on_generation_step(g)!=1)return 0;
 s->owner=getpid();s->busy=1;s->generation=g;memcpy(s->open_id,id,16);
 g->main_may_have_started=1;s->phase=WR_ON_MAIN_WAIT;
 result=wr_iot_restart_main_up();
 if(result==WR_RESTART_UP_NOT_SUBMITTED)s->phase=WR_ON_MAIN_NOT_SUBMITTED;
 s->busy=0;return result==WR_RESTART_UP_RETURNED;
}
int wr_iot_on_main_step(struct wr_iot_on_main *s)
{
 struct wr_iot_driver_identity current={0};struct wr_iot_on_generation *g;int ok=0;
 if(!s||s->owner!=getpid()||s->busy||!s->generation||
    (s->phase!=WR_ON_MAIN_WAIT&&s->phase!=WR_ON_MAIN_READY)||
    !wr_iot_rc_shutdown.active||wr_iot_rc_shutdown.pending)return 0;
 g=s->generation;
 if(g->owner!=getpid()||g->busy||!g->main_may_have_started||g->phase!=WR_ON_GEN_VERIFIED)return 0;
 s->busy=1;
 if(wr_iot_on_generation_origin_current(g)&&
    wr_iot_generated_matches(&g->admission->profile.files.generated[0],g->admission->profile.files.paths[0])&&
    wr_iot_restart_profile_current(&g->desired)&&
    wr_iot_rebind_configuration_current(&g->admission->released,s->open_id,&current)&&
    current.adapter_epoch>g->admission->released.epoch&&
    current.device_generation==g->admission->released.generation&&
    (!s->identity.adapter_epoch||(current.adapter_epoch==s->identity.adapter_epoch&&
     current.device_generation==s->identity.device_generation))&&
    wr_iot_on_generation_origin_current(g)&&!wr_iot_rc_shutdown.pending){
  s->identity=current;s->phase=WR_ON_MAIN_READY;ok=1;
 }
 s->busy=0;return ok;
}

int wr_iot_on_main_lan_step(struct wr_iot_on_main *s)
{
 int ok;
 if(!s||!wr_iot_on_main_step(s))return 0;
 s->busy=1;
 if(!s->bridge_attempted){
  s->bridge_attempted=1;
  (void)wr_iot_restart_main_bridge_attach();
 }
 ok=wr_iot_restart_main_bridge_current();s->busy=0;
 return ok&&wr_iot_on_main_step(s);
}
