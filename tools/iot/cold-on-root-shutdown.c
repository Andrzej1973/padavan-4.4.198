#define _GNU_SOURCE
#include <string.h>
#include <unistd.h>
#include "cold-on-root.h"
#include "cold-on-shutdown.h"
#include "rc-shutdown-admission.h"
int wr_iot_cold_root_shutdown(struct wr_iot_cold_root *s,
 const struct wr_iot_control_request *off)
{
 int finished=0;volatile unsigned char *bytes;size_t n;
 if(!s||s->owner!=getpid()||s->busy||s->parent.owner!=getpid()||s->parent.busy||
    !s->parent.generation.main_may_have_started||s->released.released||
    s->disabled_released.released||s->terminal.owner||s->disabled_terminal.owner||
    !wr_iot_rc_shutdown.active||!wr_iot_rc_shutdown.radio_off_owned||
    wr_iot_rc_shutdown.radio_on_owned||
    (wr_iot_rc_shutdown.pending!=SIGTERM
#ifdef SIGQUIT
     &&wr_iot_rc_shutdown.pending!=SIGQUIT
#endif
    ))return 0;
 s->busy=1;
 if(!s->handoff.owner||(s->handoff.owner==getpid()&&!s->handoff.busy&&
    s->handoff.parent==&s->parent&&s->handoff.attempted&&!s->handoff.backend_claimed&&
    s->handoff.phase==WR_COLD_HANDOFF_RETAINED)){
  /* Both saved intents are still never-opened here. The existing predicate
   * repeats backend-never-started, profile and two fresh IDLE observations. */
  if(!s->stop.owner&&!s->stop.busy&&!s->handoff.backend_claimed&&
     (s->handoff.owner||(!s->handoff.attempted&&!s->handoff.parent)))
   finished=wr_iot_cold_prehandoff_shutdown(&s->parent);
 }else if(s->enabled&&s->handoff.owner==getpid()&&!s->handoff.busy&&
          s->handoff.parent==&s->parent&&s->handoff.attempted&&s->handoff.backend_claimed){
  if(!s->stop.owner){
   if(off)(void)wr_iot_cold_postshutdown_begin(&s->stop,&s->parent,&s->handoff,off);
  }else if(s->stop.parent==&s->parent&&s->stop.handoff==&s->handoff&&
           wr_iot_cold_postshutdown_step(&s->stop))
   finished=wr_iot_rc_cold_postshutdown_release(&s->stop);
 }
 if(!finished){s->busy=0;return 0;}
 /* Child cleanup already freed credentials/guard inside the signal fence,
  * before pending signal replay. No root allocation or backend state is freed
  * here; discard only the remaining private metadata after child completion. */
 bytes=(volatile unsigned char *)s;n=sizeof(*s);while(n--)*bytes++=0;
 return 1;
}
