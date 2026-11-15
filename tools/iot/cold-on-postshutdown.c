#define _GNU_SOURCE
#include <string.h>
#include <unistd.h>
#include "cold-on-postshutdown.h"
#include "restart-guest-up.h"
#include "rc-shutdown-admission.h"
static int cold_stop_pending(void)
{
 return wr_iot_rc_shutdown.active&&wr_iot_rc_shutdown.radio_off_owned&&!wr_iot_rc_shutdown.radio_on_owned&&
  (wr_iot_rc_shutdown.pending==SIGTERM
#ifdef SIGQUIT
   ||wr_iot_rc_shutdown.pending==SIGQUIT
#endif
  );
}
int wr_iot_cold_postshutdown_begin(struct wr_iot_cold_stop *s,struct wr_iot_cold_owner *p,
 struct wr_iot_cold_handoff *h,const struct wr_iot_control_request *off)
{
 if(!s||!p||!h||!off||s->owner||s->busy||s->parent||s->handoff||s->off.owner||s->off_attempted||
    s->phase!=WR_COLD_STOP_IDLE||!cold_stop_pending()||p->owner!=getpid()||p->busy||
    h->owner!=getpid()||h->busy||h->parent!=p||!h->attempted||!h->backend_claimed||
    (h->phase!=WR_COLD_HANDOFF_WAIT&&h->phase!=WR_COLD_HANDOFF_ACTIVE)||
    !h->created||!memchr(h->id,0,sizeof(h->id))||!wr_iot_control_id(h->id)||
    !off->created||off->created<h->created||off->request.enabled||
    !memchr(off->id,0,sizeof(off->id))||!wr_iot_control_id(off->id)||!strcmp(off->id,h->id)||
    off->request.ssid[0]||off->request.password[0]||off->request.gateway[0]||
    off->request.mask[0]||off->request.first[0]||off->request.last[0])return 0;
 s->owner=getpid();s->parent=p;s->handoff=h;s->phase=WR_COLD_STOP_ADMITTED;
 memcpy(s->input.id,off->id,sizeof(s->input.id));s->input.created=off->created;return 1;
}
int wr_iot_cold_postshutdown_step(struct wr_iot_cold_stop *s)
{
 struct wr_iot_driver_closed_result closed={0};struct wr_iot_cold_owner *p;int result=0,guest;
 if(!s||s->owner!=getpid()||s->busy||!s->parent||!s->handoff||!cold_stop_pending())return 0;
 p=s->parent;
 if(p->owner!=getpid()||p->busy||s->handoff->parent!=p||s->handoff->owner!=getpid()||s->handoff->busy||
    p->guest.busy||(p->guest.owner&&(p->guest.owner!=getpid()||p->guest.main!=&p->main)))return 0;
 s->busy=1;
 if(p->guest.owner)(void)wr_iot_cold_guest_step(&p->guest);
 if(!wr_iot_restart_guest_admin_state(&guest)||guest)goto done;
 if(s->phase==WR_COLD_STOP_CLOSED){result=wr_iot_rc_cold_shutdown_closed(p,s->handoff,&s->off,&closed);goto done;}
 if(s->phase==WR_COLD_STOP_REJECTED){result=wr_iot_rc_cold_shutdown_rejected(p,s->handoff);goto done;}
 if(s->phase==WR_COLD_STOP_ADMITTED){
  if(wr_iot_rc_cold_shutdown_rejected(p,s->handoff)){s->phase=WR_COLD_STOP_REJECTED;result=1;goto done;}
  if(!wr_iot_rc_cold_shutdown_advance(p,s->handoff))goto done;
  if(s->off_attempted)goto done;
  s->off_attempted=1;s->phase=WR_COLD_STOP_RETAINED;
  if(wr_iot_rc_cold_shutdown_off_begin(p,s->handoff,&s->off,&s->input))s->phase=WR_COLD_STOP_DRAIN;
  goto done;
 }
 if(s->phase==WR_COLD_STOP_DRAIN&&wr_iot_rc_quiesce_advance(&s->off,&closed)&&
    wr_iot_rc_cold_shutdown_closed(p,s->handoff,&s->off,&closed)){
  s->phase=WR_COLD_STOP_CLOSED;result=1;
 }
 done:s->busy=0;return result;
}
