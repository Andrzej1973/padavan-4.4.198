#define _GNU_SOURCE
#include <string.h>
#include <unistd.h>
#include "radio-on-restore.h"
#include "restart-radio-state.h"
#include "radio-on-aux.h"
#include "rc-shutdown-admission.h"
int wr_iot_on_restore_begin(struct wr_iot_on_restore *s,struct wr_iot_on_admission *a,
 const struct wr_iot_request *desired,int reload,const unsigned char *id)
{
 unsigned i,nonzero=0;
 if(!s||!a||!desired||!id||s->owner||s->busy||s->radio_state_attempted||s->phase!=WR_ON_RESTORE_IDLE||
    s->wan.owner||s->terminal.owner||s->child.owner||s->child.attempted||s->led_attempted||s->led_returned||
    s->generation.owner||s->main.owner||s->guest.owner||s->services.owner||s->multicast.owner||
    !wr_iot_rc_shutdown.active||wr_iot_rc_shutdown.pending)return 0;
 for(i=0;i<16;i++)nonzero|=id[i];
 if(!nonzero)return 0;
 s->owner=getpid();s->busy=1;memcpy(s->open_id,id,16);s->phase=WR_ON_RESTORE_RETAINED;
 if(wr_iot_on_generation_begin(&s->generation,a,desired,reload))s->phase=WR_ON_RESTORE_PROFILE;
 s->busy=0;return s->phase==WR_ON_RESTORE_PROFILE;
}
int wr_iot_on_restore_step(struct wr_iot_on_restore *s)
{
 int ok=0;
 if(!s||s->owner!=getpid()||s->busy||!wr_iot_rc_shutdown.active)return 0;
 s->busy=1;
 if(wr_iot_rc_shutdown.pending){
  if(s->generation.owner==getpid()&&!s->generation.main_may_have_started)
   (void)wr_iot_on_generation_recover(&s->generation);
  /* Only Guest's own submitted UP can authorize its bounded DOWN recovery.
   * Profile/Main and outer ownership remain retained for root cleanup. */
  if(s->guest.owner)(void)wr_iot_on_guest_step(&s->guest);
  goto done;
 }
 if(s->generation.main_may_have_started&&!wr_iot_on_aux_down_current())goto done;
 switch(s->phase){
 case WR_ON_RESTORE_PROFILE:
  if(wr_iot_on_generation_step(&s->generation))s->phase=WR_ON_RESTORE_MAIN_START;
  break;
 case WR_ON_RESTORE_MAIN_START:
  if(s->radio_state_attempted||!wr_iot_on_generation_step(&s->generation))break;
  s->radio_state_attempted=1;s->phase=WR_ON_RESTORE_RETAINED;
  if(!wr_iot_rc_restart_radio_state(s->generation.reload)||wr_iot_rc_shutdown.pending)break;
  s->phase=WR_ON_RESTORE_MAIN_WAIT;
  (void)wr_iot_on_main_begin(&s->main,&s->generation,s->open_id);
  if(!s->main.owner)s->phase=WR_ON_RESTORE_RETAINED;
  break;
 case WR_ON_RESTORE_MAIN_WAIT:
  if(wr_iot_on_main_lan_step(&s->main))s->phase=WR_ON_RESTORE_GUEST_BEGIN;
  break;
 case WR_ON_RESTORE_GUEST_BEGIN:
  if(wr_iot_on_guest_begin(&s->guest,&s->main))s->phase=WR_ON_RESTORE_GUEST_WAIT;
  break;
 case WR_ON_RESTORE_GUEST_WAIT:
  if(wr_iot_on_guest_step(&s->guest))s->phase=WR_ON_RESTORE_MC_BEGIN;
  break;
 case WR_ON_RESTORE_MC_BEGIN:
  if(wr_iot_on_multicast_begin(&s->multicast,&s->main,&s->guest))s->phase=WR_ON_RESTORE_MC_WAIT;
  break;
 case WR_ON_RESTORE_MC_WAIT:
  if(wr_iot_on_multicast_step(&s->multicast))s->phase=WR_ON_RESTORE_SERVICE_BEGIN;
  break;
 case WR_ON_RESTORE_SERVICE_BEGIN:
  if(!wr_iot_on_multicast_step(&s->multicast))break;
  if(wr_iot_on_services_begin(&s->services,&s->guest))s->phase=WR_ON_RESTORE_SERVICE_WAIT;
  break;
 case WR_ON_RESTORE_SERVICE_WAIT:
 case WR_ON_RESTORE_PREPARED:
  if(!wr_iot_on_multicast_step(&s->multicast))break;
  if(wr_iot_on_services_step(&s->services)){s->phase=WR_ON_RESTORE_PREPARED;ok=1;}
  break;
 default:break;
 }
 done:s->busy=0;return ok;
}
