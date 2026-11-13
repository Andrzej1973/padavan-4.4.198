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
static int off_current(void)
{
 return wr_iot_request_initial_off_current()&&!if_nametoindex("br-iot")&&
  wr_iot_bss_is_down()&&wr_iot_dns_activation_recovery_state()==0;
}
int wr_iot_initial_off_begin(struct wr_iot_initial_off *s,const struct wr_iot_control_request *r)
{
 struct wr_iot_initial_off candidate={0};struct wr_iot_idle_result before,after;
 unsigned i,nonzero=0;int guard,ok=0;
 if(!s||!r||s->owner||s->ready||!wr_iot_rc_shutdown.active||
    wr_iot_rc_shutdown.pending||r->request.enabled!=0||!r->created||
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
    wr_iot_rc_shutdown.pending||!off_current())goto done;
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
