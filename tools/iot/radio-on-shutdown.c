#define _GNU_SOURCE
#include <string.h>
#include <unistd.h>
#include "radio-on-shutdown.h"
#include "control-channel.h"
#include "rc-shutdown-admission.h"
static int on_stop_pending(void)
{
 return wr_iot_rc_shutdown.active&&(wr_iot_rc_shutdown.pending==SIGTERM
#ifdef SIGQUIT
  ||wr_iot_rc_shutdown.pending==SIGQUIT
#endif
 );
}
int wr_iot_on_shutdown_begin(struct wr_iot_on_shutdown *s,struct wr_iot_on_restore *r,
 const struct wr_iot_control_request *off)
{
 static const char hex[]="0123456789abcdef";char on_id[33]={0};unsigned i;
 if(!s||!r||!off||s->owner||s->busy||s->restore||s->off.owner||s->phase!=WR_ON_STOP_IDLE||
    !on_stop_pending()||r->owner!=getpid()||r->busy||r->phase!=WR_ON_RESTORE_HANDOFF||
    !r->handoff_created||!r->generation.admission||!r->generation.main_may_have_started||
    off->request.enabled!=0||!off->created||off->created<r->handoff_created||
    !memchr(off->id,0,sizeof(off->id))||!wr_iot_control_id(off->id))return 0;
 for(i=0;i<16;i++){on_id[2*i]=hex[r->open_id[i]>>4];on_id[2*i+1]=hex[r->open_id[i]&15];}
 if(!strcmp(on_id,off->id)||!wr_iot_on_generation_origin_current(&r->generation))return 0;
 memcpy(s->input.id,off->id,sizeof(off->id));s->input.created=off->created;
 s->owner=getpid();s->restore=r;s->phase=WR_ON_STOP_ADMITTED;return 1;
}
int wr_iot_on_shutdown_step(struct wr_iot_on_shutdown *s)
{
 struct wr_iot_driver_closed_result closed={0};struct wr_iot_on_restore *r;int result=0;
 char on_id[33]={0};static const char hex[]="0123456789abcdef";unsigned i;
 if(!s||s->owner!=getpid()||s->busy||!s->restore||!on_stop_pending())return 0;
 r=s->restore;
 if(r->owner!=getpid()||r->busy||r->phase!=WR_ON_RESTORE_HANDOFF||
    !r->generation.admission||!wr_iot_on_generation_origin_current(&r->generation))return 0;
 s->busy=1;
 /* Pending Guest controller drains only its already-submitted UP. */
 if(r->guest.owner)(void)wr_iot_on_guest_step(&r->guest);
 if(s->phase==WR_ON_STOP_CLOSED||s->phase==WR_ON_STOP_REJECTED){
  result=wr_iot_on_shutdown_closed_current(r,s->phase==WR_ON_STOP_CLOSED?&s->off:NULL);goto done;
 }
 if(s->phase==WR_ON_STOP_ADMITTED){
  for(i=0;i<16;i++){on_id[2*i]=hex[r->open_id[i]>>4];on_id[2*i+1]=hex[r->open_id[i]&15];}
  /* Existing stable backend owner advances, never another OPEN begin. */
  (void)wr_iot_activation_continue(on_id,r->handoff_created);
  if(wr_iot_on_shutdown_rejected_current(r)){
   s->phase=WR_ON_STOP_REJECTED;
   result=wr_iot_on_shutdown_closed_current(r,NULL);goto done;
  }
  if(wr_iot_rc_quiesce_shutdown_begin(&s->off,&s->input))s->phase=WR_ON_STOP_DRAIN;
  goto done;
 }
 if(s->phase==WR_ON_STOP_DRAIN&&wr_iot_rc_quiesce_advance(&s->off,&closed)){
  if(wr_iot_on_shutdown_closed_current(r,&s->off)){s->phase=WR_ON_STOP_CLOSED;result=1;}
 }
 done:s->busy=0;return result;
}
