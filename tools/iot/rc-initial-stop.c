#include <string.h>
#include <unistd.h>
#include <time.h>
#include "rc-initial-stop.h"
#include "rc-backend.h"
#include "rc-physical-stop.h"
#include "rc-shutdown-admission.h"
#include "service-guard.h"
static int initial_stop_begin_mode(struct wr_iot_rc_initial_stop *s,const unsigned char *nonce,
 const struct wr_iot_initial_shutdown_owner *shutdown)
{
 unsigned i,nonzero=0;
 if(!s||!nonce||s->owner||s->busy||s->result||s->aux_next||s->auth.owner||
    s->session.owner||s->shutdown||!wr_iot_rc_shutdown.active||
    (shutdown?!wr_iot_initial_shutdown_current(shutdown):wr_iot_rc_shutdown.pending))return 0;
 for(i=0;i<16;i++)nonzero|=nonce[i];
 if(!nonzero)return 0;
 memcpy(s->nonce,nonce,16);s->shutdown=shutdown;s->owner=getpid();return 1;
}
int wr_iot_rc_initial_stop_begin(struct wr_iot_rc_initial_stop *s,const unsigned char *nonce)
{return initial_stop_begin_mode(s,nonce,NULL);}
int wr_iot_rc_initial_stop_begin_shutdown(struct wr_iot_rc_initial_stop *s,const unsigned char *nonce,const struct wr_iot_initial_shutdown_owner *owner)
{return owner&&wr_iot_initial_shutdown_current(owner)&&initial_stop_begin_mode(s,nonce,owner);}
int wr_iot_rc_initial_stop_step(struct wr_iot_rc_initial_stop *s)
{
 struct wr_iot_physical_initial_request request={0};struct timespec now;
 unsigned long long ms;int guard,result=0;
 if(!s||s->owner!=getpid()||s->busy)return 0;
 if(s->result)return s->result;
 if(!wr_iot_rc_shutdown.active||(s->shutdown&&!wr_iot_initial_shutdown_current(s->shutdown)))return 0;
 guard=wr_iot_service_guard_enter(1);if(guard!=1)return 0;
 s->busy=1;
 if(s->session.phase==WR_INITIAL_PHYSICAL_SESSION_IDLE){
  if(s->shutdown?!wr_iot_initial_shutdown_current(s->shutdown):wr_iot_rc_shutdown.pending)goto done;
  if(clock_gettime(CLOCK_MONOTONIC,&now)||now.tv_sec<=0)goto done;
  ms=(unsigned long long)now.tv_sec*1000+(unsigned long long)now.tv_nsec/1000000;
  if(!s->auth.owner){(void)wr_iot_auth_stop_begin(&s->auth,ms);goto done;}
  if(!wr_iot_auth_stop_step(&s->auth,ms))goto done;
  if(s->aux_next<6){
   if(wr_iot_rc_physical_aux_down(s->aux_next)==1)s->aux_next++;
   goto done;
  }
  /* AUX may change registry observations. Obtain a fresh exact initial ARM
   * only after all six administrative closures; never fabricate CLOSE. */
  if(s->shutdown?wr_iot_rc_backend_shutdown_initial_request(s->shutdown,s->nonce,&request):
     wr_iot_rc_backend_prepared_initial_request(s->nonce,&request))
   (void)wr_iot_initial_physical_session_begin(&s->session,&request);
 }else result=wr_iot_initial_physical_session_advance(&s->session);
 if(result)s->result=result;
 done:s->busy=0;wr_iot_service_guard_leave(guard);return result;
}
int wr_iot_rc_initial_stop_released(const struct wr_iot_rc_initial_stop *s,
 struct wr_iot_physical_initial_request *out)
{
 if(!out)return 0;
 memset(out,0,sizeof(*out));
 if(!s||s->owner!=getpid()||s->busy||s->result!=1||s->aux_next!=6||
    s->session.owner!=getpid()||s->session.busy||
    s->session.phase!=WR_INITIAL_PHYSICAL_SESSION_COMPLETE||
    s->session.request.action!=WR_STOP_QUERY||
    !wr_iot_physical_initial_valid(&s->session.request,0))return 0;
 *out=s->session.request;out->action=WR_STOP_RELEASE;return 1;
}
