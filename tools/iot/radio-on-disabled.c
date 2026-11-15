#define _GNU_SOURCE
#include <string.h>
#include <unistd.h>
#include "radio-on-disabled.h"
#include "rc-shutdown-admission.h"
static int disabled_parent(struct wr_iot_on_restore *r)
{
 return r&&r->owner==getpid()&&!r->busy&&r->phase==WR_ON_RESTORE_PREPARED&&
  r->generation.desired.enabled==0&&r->generation.admission&&
  r->generation.owner==getpid()&&r->generation.main_may_have_started&&
  r->main.generation==&r->generation&&r->guest.main==&r->main&&
  r->services.guest==&r->guest&&r->multicast.main==&r->main&&
  r->multicast.guest==&r->guest&&!r->handoff_created&&
  !r->wan.owner&&!r->terminal.owner&&!r->child.owner&&!r->child.attempted&&
  wr_iot_rc_shutdown.active&&!wr_iot_rc_shutdown.pending&&
  wr_iot_on_restore_step(r)==1;
}
int wr_iot_on_disabled_current(struct wr_iot_on_disabled *s)
{
 int ok;
 if(!s||s->owner!=getpid()||s->busy||!disabled_parent(s->restore))return 0;
 s->busy=1;
 ok=wr_iot_initial_off_restarted_observed(&s->idle,
  &s->restore->generation.admission->released,&s->restore->main.identity)&&
  disabled_parent(s->restore);
 s->busy=0;return ok;
}
int wr_iot_on_disabled_begin(struct wr_iot_on_disabled *s,struct wr_iot_on_restore *r,
 const struct wr_iot_control_request *request)
{
 if(!s||!request||s->owner||s->busy||s->restore||s->idle.owner||
    request->request.enabled!=0||!disabled_parent(r))return 0;
 s->busy=1;
 if(!wr_iot_initial_off_begin(&s->idle,request)){s->busy=0;return 0;}
 /* Retain the captured identity even if the next observation refuses. */
 s->owner=getpid();s->restore=r;
 s->busy=0;return wr_iot_on_disabled_current(s);
}
