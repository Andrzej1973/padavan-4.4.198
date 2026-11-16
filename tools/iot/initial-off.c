#include "initial-shutdown-owner.h"
#include <string.h>
#include <unistd.h>
#include <net/if.h>
#include "initial-off.h"
#include "request-snapshot.h"
#include "service-guard.h"
#include "rc-shutdown-admission.h"
#include "driver-api-client.h"
#include "bridge.h"
#include "dns-activation.h"
static int initial_signal_allowed(const struct wr_iot_initial_shutdown_owner *owner)
{return owner?wr_iot_initial_shutdown_current(owner):!wr_iot_rc_shutdown.pending;}
static int off_current(void)
{
 return wr_iot_request_initial_off_current()&&!if_nametoindex("br-iot")&&
  wr_iot_bss_is_down()&&wr_iot_dns_activation_recovery_state()==0;
}
static int wr_iot_initial_off_begin_mode(struct wr_iot_initial_off *s,const struct wr_iot_control_request *r,
 const struct wr_iot_initial_shutdown_owner *owner)
{
 struct wr_iot_initial_off candidate={0};struct wr_iot_idle_result before,after;
 unsigned i,nonzero=0;int guard,ok=0;
 if(!s||!r||s->owner||s->ready||!wr_iot_rc_shutdown.active||
    !initial_signal_allowed(owner)||r->request.enabled!=0||!r->created||
    !memchr(r->id,0,sizeof(r->id))||!wr_iot_control_id(r->id))return 0;
 for(i=0;i<16;i++){
  unsigned char a=r->id[2*i],b=r->id[2*i+1];
  candidate.nonce[i]=(unsigned char)(((a<='9'?a-'0':a-'a'+10)<<4)|(b<='9'?b-'0':b-'a'+10));
  nonzero|=candidate.nonce[i];
 }
 if(!nonzero)return 0;
 guard=wr_iot_service_guard_enter(1);if(guard!=1)return 0;
 if(!off_current()||!wr_iot_driver_initial_idle_read(candidate.nonce,&before)||
    !off_current()||!wr_iot_driver_initial_idle_read(candidate.nonce,&after)||
    !before.epoch||!before.generation||!before.serial||
    before.epoch!=after.epoch||before.generation!=after.generation||after.serial<=before.serial||
    !initial_signal_allowed(owner)||!off_current())goto done;
 candidate.owner=getpid();candidate.created=r->created;candidate.idle=after;candidate.ready=1;
 memcpy(candidate.id,r->id,sizeof(candidate.id));*s=candidate;ok=1;
 done:wr_iot_service_guard_leave(guard);return ok;
}
int wr_iot_initial_off_observed(const struct wr_iot_initial_off *s)
{
 struct wr_iot_idle_result current;
 if(!s||s->owner!=getpid()||!s->ready||!s->created||
    !memchr(s->id,0,sizeof(s->id))||!wr_iot_control_id(s->id))return 0;
 return off_current()&&wr_iot_driver_initial_idle_read(s->nonce,&current)&&
  current.epoch==s->idle.epoch&&current.generation==s->idle.generation&&
  current.serial>s->idle.serial&&off_current();
}

int wr_iot_initial_off_restarted_observed(const struct wr_iot_initial_off *s,
 const struct wr_iot_physical_stop_request *released,const struct wr_iot_driver_identity *main)
{
 if(!s||!released||!main||released->action!=WR_STOP_RELEASE||
    !wr_iot_physical_stop_request_valid(released)||!main->adapter_epoch||
    !main->device_generation||main->adapter_epoch<=released->epoch||
    main->device_generation!=released->generation||
    s->idle.epoch!=main->adapter_epoch||s->idle.generation!=main->device_generation||
    !wr_iot_rc_shutdown.active||wr_iot_rc_shutdown.pending)return 0;
 return wr_iot_initial_off_observed(s);
}

static int wr_iot_initial_off_physical_request_mode(const struct wr_iot_initial_off *s,
 const unsigned char *nonce,struct wr_iot_physical_initial_request *out,
 const struct wr_iot_initial_shutdown_owner *owner)
{
 struct wr_iot_idle_result current={0};
 struct wr_iot_physical_initial_request candidate={0};unsigned i;
 if(!out)return 0;
 memset(out,0,sizeof(*out));
 if(!s||!nonce||s->owner!=getpid()||!s->ready||!s->created||
    !memchr(s->id,0,sizeof(s->id))||!wr_iot_control_id(s->id)||
    !wr_iot_rc_shutdown.active||!initial_signal_allowed(owner)||!off_current())return 0;
 if(!wr_iot_driver_initial_idle_read(s->nonce,&current)||
    current.epoch!=s->idle.epoch||current.generation!=s->idle.generation||
    current.serial<=s->idle.serial||!off_current()||!initial_signal_allowed(owner))return 0;
 candidate.action=WR_STOP_ARM;candidate.epoch=current.epoch;
 candidate.generation=current.generation;candidate.idle_serial=current.serial;
 for(i=0;i<16;i++)candidate.nonce[i]=nonce[i];
 if(!wr_iot_physical_initial_valid(&candidate,0))return 0;
 *out=candidate;return 1;
}

static int initial_main_probe(const struct wr_iot_physical_initial_request *released,
 const unsigned char *nonce,struct wr_iot_driver_identity *out)
{
 struct wr_iot_idle_result before={0},after={0};
 if(!out)return 0;
 memset(out,0,sizeof(*out));
 if(!released||released->action!=WR_STOP_RELEASE||
    !wr_iot_physical_initial_valid(released,0)||!nonce||
    wr_iot_rc_shutdown.pending||!off_current())return 0;
 if(!wr_iot_driver_initial_idle_read(nonce,&before)||!off_current()||
    !wr_iot_driver_initial_idle_read(nonce,&after)||
    before.epoch<=released->epoch||before.generation!=released->generation||
    !before.serial||after.serial<=before.serial||before.epoch!=after.epoch||
    before.generation!=after.generation||wr_iot_rc_shutdown.pending||!off_current())return 0;
 out->adapter_epoch=after.epoch;out->device_generation=after.generation;return 1;
}

int wr_iot_initial_main_current(const struct wr_iot_physical_initial_request *released,
 const unsigned char *nonce,struct wr_iot_driver_identity *out)
{
 if(!out)return 0;
 memset(out,0,sizeof(*out));
 return wr_iot_rc_shutdown.active&&initial_main_probe(released,nonce,out);
}
int wr_iot_initial_postrelease_current(const struct wr_iot_physical_initial_request *released,
 const unsigned char *nonce,const struct wr_iot_driver_identity *expected)
{
 struct wr_iot_driver_identity observed={0};int guard,ok;
 if(!expected||!expected->adapter_epoch||!expected->device_generation||
    wr_iot_rc_shutdown.active||wr_iot_rc_shutdown.pending)return 0;
 guard=wr_iot_service_guard_enter(1);if(guard!=1)return 0;
 ok=!wr_iot_rc_shutdown.active&&!wr_iot_rc_shutdown.pending&&
  initial_main_probe(released,nonce,&observed)&&
  observed.adapter_epoch==expected->adapter_epoch&&
  observed.device_generation==expected->device_generation&&
  !wr_iot_rc_shutdown.active&&!wr_iot_rc_shutdown.pending;
 wr_iot_service_guard_leave(guard);return ok;
}

int wr_iot_initial_off_begin(struct wr_iot_initial_off *s,const struct wr_iot_control_request *r)
{return wr_iot_initial_off_begin_mode(s,r,NULL);}
int wr_iot_initial_off_physical_request(const struct wr_iot_initial_off *s,const unsigned char *n,struct wr_iot_physical_initial_request *q)
{return wr_iot_initial_off_physical_request_mode(s,n,q,NULL);}
int wr_iot_initial_off_begin_shutdown(struct wr_iot_initial_off *s,const struct wr_iot_control_request *r,const struct wr_iot_initial_shutdown_owner *o)
{return o&&wr_iot_initial_shutdown_current(o)&&wr_iot_initial_off_begin_mode(s,r,o);}
int wr_iot_initial_off_request_shutdown(const struct wr_iot_initial_off *s,const unsigned char *n,struct wr_iot_physical_initial_request *q,const struct wr_iot_initial_shutdown_owner *o)
{if(q)memset(q,0,sizeof(*q));return o&&wr_iot_initial_shutdown_current(o)&&wr_iot_initial_off_physical_request_mode(s,n,q,o);}
