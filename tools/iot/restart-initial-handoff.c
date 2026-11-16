#define _GNU_SOURCE
#include <string.h>
#include <unistd.h>
#include "restart-initial-handoff.h"
#include "rc-quiesce.h"
#include "rc-shutdown-admission.h"
static void initial_request_wipe(struct wr_iot_control_request *r)
{volatile unsigned char*p=(volatile unsigned char*)r;size_t n=sizeof(*r);while(n--)*p++=0;}
int wr_iot_restart_initial_handoff_begin(struct wr_iot_restart_restore *s,
 const struct wr_iot_control_request *r)
{
 unsigned i;unsigned char id[16];int claimed;
 if(!s||!r||s->owner!=getpid()||s->busy||s->phase!=WR_RESTORE_PREPARED||
    s->handoff_created||s->initial_start_claimed||s->generation.origin.origin!=WR_PHYSICAL_ORIGIN_INITIAL||
    s->generation.origin.resume_needed!=1||s->generation.origin.desired.enabled!=1||
    r->request.enabled!=1||!r->created||!memchr(r->id,0,sizeof(r->id))||!wr_iot_control_id(r->id)||
    !wr_iot_rc_shutdown.active||wr_iot_rc_shutdown.pending)return 0;
 for(i=0;i<16;i++){
  unsigned char a=r->id[2*i],b=r->id[2*i+1];
  id[i]=(unsigned char)(((a<='9'?a-'0':a-'a'+10)<<4)|(b<='9'?b-'0':b-'a'+10));
 }
 if(memcmp(id,s->open_id,16))return 0;
#define SAME(f) if(!memchr(r->request.f,0,sizeof(r->request.f))||strcmp(r->request.f,s->generation.origin.desired.f))return 0;
 SAME(ssid) SAME(password) SAME(gateway) SAME(mask) SAME(first) SAME(last)
#undef SAME
 if(!wr_iot_restart_restore_step(s))return 0;
 /* Retain the first attempt before calling an external backend. Refusal
  * cannot be converted into an automatic second START. */
 s->busy=1;s->phase=WR_RESTORE_HANDOFF;s->handoff_created=r->created;
 claimed=wr_iot_rc_initial_restart_start_begin(s,r);
 s->initial_start_claimed=claimed==1;s->busy=0;return claimed==1;
}
static int initial_handoff_observe(struct wr_iot_restart_restore *s,int progress)
{
 struct wr_iot_control_request r={0};static const char hex[]="0123456789abcdef";
 unsigned i;int active=0;
 if(!s||s->owner!=getpid()||s->busy||s->phase!=WR_RESTORE_HANDOFF||
    s->initial_start_claimed!=1||!s->handoff_created||
    s->generation.origin.origin!=WR_PHYSICAL_ORIGIN_INITIAL||
    s->generation.origin.resume_needed!=1||s->generation.origin.desired.enabled!=1||
    !wr_iot_rc_shutdown.active||wr_iot_rc_shutdown.pending||
    !wr_iot_restart_generation_origin_current(&s->generation))return 0;
 for(i=0;i<16;i++){r.id[2*i]=hex[s->open_id[i]>>4];r.id[2*i+1]=hex[s->open_id[i]&15];}
 r.created=s->handoff_created;r.request=s->generation.origin.desired;s->busy=1;
 /* After START, never-opened idle is no longer the appropriate observer.
  * Advance only the bound backend owner, then require full ACTIVE proof. */
 active=wr_iot_rc_initial_restart_active_current(s,&r);
 if(!active&&progress&&wr_iot_rc_initial_restart_start_progress(s,&r))
  active=wr_iot_rc_initial_restart_active_current(s,&r);
 active=active&&wr_iot_restart_generation_origin_current(&s->generation)&&
  !wr_iot_rc_shutdown.pending;
 initial_request_wipe(&r);s->busy=0;return active;
}

int wr_iot_restart_initial_handoff_step(struct wr_iot_restart_restore *s)
{return initial_handoff_observe(s,1);}
int wr_iot_restart_initial_active_current(struct wr_iot_restart_restore *s)
{return initial_handoff_observe(s,0);}

int wr_iot_restart_initial_cancel_step(struct wr_iot_restart_restore *s)
{
 struct wr_iot_control_request r={0};static const char hex[]="0123456789abcdef";
 unsigned i;int rejected;
 if(!s||s->owner!=getpid()||s->busy||s->phase!=WR_RESTORE_HANDOFF||
    (s->initial_start_claimed!=0&&s->initial_start_claimed!=1)||!s->handoff_created||
    s->generation.origin.origin!=WR_PHYSICAL_ORIGIN_INITIAL||
    s->generation.origin.resume_needed!=1||s->generation.origin.desired.enabled!=1||
    !wr_iot_rc_shutdown.active||
    (wr_iot_rc_shutdown.pending!=SIGTERM
#ifdef SIGQUIT
     &&wr_iot_rc_shutdown.pending!=SIGQUIT
#endif
    )||!wr_iot_restart_generation_origin_current(&s->generation))return 0;
 for(i=0;i<16;i++){r.id[2*i]=hex[s->open_id[i]>>4];r.id[2*i+1]=hex[s->open_id[i]&15];}
 r.created=s->handoff_created;r.request=s->generation.origin.desired;s->busy=1;
 if(!s->initial_start_claimed)rejected=wr_iot_rc_initial_restart_unclaimed_current(s,&r);
 else{
  rejected=wr_iot_rc_initial_restart_preopen_rejected(s,&r)||(wr_iot_rc_initial_restart_rollback_closed(s,&r)||wr_iot_rc_initial_restart_committed_closed(s,&r));
  if(!rejected&&wr_iot_rc_initial_restart_cancel_progress(s,&r))
   rejected=wr_iot_rc_initial_restart_preopen_rejected(s,&r)||(wr_iot_rc_initial_restart_rollback_closed(s,&r)||wr_iot_rc_initial_restart_committed_closed(s,&r));
 }
 rejected=rejected&&wr_iot_restart_generation_origin_current(&s->generation);
 initial_request_wipe(&r);s->busy=0;return rejected;
}

int wr_iot_restart_initial_shutdown_step(struct wr_iot_restart_restore *s,
 const struct wr_iot_control_request *off,struct wr_iot_rc_quiesce *q)
{
 struct wr_iot_control_request r={0};struct wr_iot_driver_closed_result closed={0};
 static const char hex[]="0123456789abcdef";unsigned i;int done=0;
 if(!s||!off||!q||s->owner!=getpid()||s->busy||s->phase!=WR_RESTORE_HANDOFF||
    (s->initial_start_claimed!=0&&s->initial_start_claimed!=1)||!s->handoff_created||
    s->generation.origin.origin!=WR_PHYSICAL_ORIGIN_INITIAL||
    s->generation.origin.resume_needed!=1||s->generation.origin.desired.enabled!=1||
    !wr_iot_rc_shutdown.active||
    (wr_iot_rc_shutdown.pending!=SIGTERM
#ifdef SIGQUIT
     &&wr_iot_rc_shutdown.pending!=SIGQUIT
#endif
    )||!wr_iot_restart_generation_origin_current(&s->generation))return 0;
 if(!q->owner&&wr_iot_restart_initial_cancel_step(s))return 1;
 if(!s->initial_start_claimed)return 0;
 for(i=0;i<16;i++){r.id[2*i]=hex[s->open_id[i]>>4];r.id[2*i+1]=hex[s->open_id[i]&15];}
 r.created=s->handoff_created;r.request=s->generation.origin.desired;s->busy=1;
 if(!q->owner)(void)wr_iot_rc_initial_restart_shutdown_begin(s,&r,off,q);
 else if(wr_iot_rc_initial_restart_shutdown_progress(s,&r,q,&closed))done=2;
 initial_request_wipe(&r);s->busy=0;return done;
}
