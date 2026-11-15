#define _GNU_SOURCE
#include <unistd.h>
#include "cold-on-services.h"
#include "rc-shutdown-admission.h"
static int same_policy(const struct wr_iot_restart_service_policy *a,
 const struct wr_iot_restart_service_policy *b)
{return a->enterprise==b->enterprise&&a->kick_rssi==b->kick_rssi&&a->assoc_rssi==b->assoc_rssi;}
int wr_iot_cold_services_begin(struct wr_iot_cold_services *s,struct wr_iot_cold_guest *guest)
{
 struct wr_iot_restart_service_policy p;
 if(!s||!guest||s->owner||s->busy||s->phase!=WR_COLD_SERVICES_IDLE||s->next||s->attempted||
    !wr_iot_rc_shutdown.active||wr_iot_rc_shutdown.pending||
    !wr_iot_cold_guest_step(guest)||!wr_iot_rc_restart_service_policy(&p)||
    wr_iot_rc_shutdown.pending)return 0;
 s->owner=getpid();s->guest=guest;s->policy=p;s->phase=WR_COLD_SERVICES_SUBMIT;return 1;
}
int wr_iot_cold_services_step(struct wr_iot_cold_services *s)
{
 struct wr_iot_restart_service_policy current;enum wr_iot_restart_service_result result;int ok=0;
 if(!s||s->owner!=getpid()||s->busy||!s->guest||s->next>3||
    (s->phase!=WR_COLD_SERVICES_SUBMIT&&s->phase!=WR_COLD_SERVICES_SUBMITTED)||
    !wr_iot_rc_shutdown.active||wr_iot_rc_shutdown.pending)return 0;
 s->busy=1;
 if(!wr_iot_cold_guest_step(s->guest)||!wr_iot_rc_restart_service_policy(&current)||
    !same_policy(&s->policy,&current)||wr_iot_rc_shutdown.pending)goto done;
 if(s->phase==WR_COLD_SERVICES_SUBMITTED){ok=s->next==3&&s->attempted==7;goto done;}
 if(s->next>=3||s->attempted&(1U<<s->next))goto done;
 s->attempted|=1U<<s->next;s->phase=WR_COLD_SERVICES_UNCERTAIN;
 result=wr_iot_rc_restart_service_submit(&s->policy,s->next);
 /* Even NOT_SUBMITTED remains retained: no automatic mutation retries. */
 if(result==WR_SERVICE_RETURNED){
  s->next++;s->phase=s->next==3?WR_COLD_SERVICES_SUBMITTED:WR_COLD_SERVICES_SUBMIT;
 }
 done:s->busy=0;return ok;
}
