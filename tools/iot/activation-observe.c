#include <string.h>
#include <unistd.h>
#include <net/if.h>
#include "activation-observe.h"
#include "service-guard.h"
#include "request-stage.h"
#include "network-check.h"
#include "bridge.h"
#include "quarantine.h"
#include "dns-activation.h"
int wr_iot_activation_owner_observed(const struct wr_iot_activation_owner *s,
 const struct wr_iot_control_result *r)
{
 const struct wr_iot_start_runner *a;int guard,ok=0;
 if(!s||!r||s->owner!=getpid()||s->busy||r->state!=WR_IOT_RESULT_APPLIED||
    !r->created||!memchr(r->id,0,sizeof(r->id))||!wr_iot_control_id(r->id))return 0;
 if(s->phase==WR_IOT_OWNER_INITIAL_OFF){
  if(strcmp(r->id,s->initial_off.id)||r->created!=s->initial_off.created)return 0;
  guard=wr_iot_service_guard_enter(1);if(guard!=1)return 0;
  ok=wr_iot_initial_off_observed(&s->initial_off);
  wr_iot_service_guard_leave(guard);return ok;
 }
 a=&s->start;
 if(a->owner!=getpid()||a->busy)return 0;
 guard=wr_iot_service_guard_enter(1);if(guard!=1)return 0;
 if(s->phase==WR_IOT_OWNER_ACTIVE&&a->phase==WR_IOT_RUN_ACTIVE&&
    a->commit.phase==WR_IOT_COMMIT_ACTIVE&&a->commit.owner==getpid()&&
    a->open.owner==getpid()&&a->open.phase==WR_IOT_OPEN_CONFIRMED&&
    a->network.phase==WR_IOT_NET_READY&&
    !strcmp(r->id,a->input.id)&&r->created==a->input.created){
  struct wr_iot_driver_open_current_result current;
  const struct wr_iot_request *request=&a->input.request;
  ok=wr_iot_request_snapshot_expected_current(&a->admission.snapshot)&&
   wr_iot_request_stage_matches(request)&&
   wr_iot_network_check(request->gateway,request->mask,request->first,request->last)&&
   wr_iot_bridge_address_matches(request->gateway,request->mask)&&
   wr_iot_network_services_ready(request->gateway)&&
   wr_iot_active_filter_observed_current()&&
   wr_iot_driver_open_current_read(&a->open.attempt,&current)&&
   current.adapter_epoch==a->open.attempt.identity.adapter_epoch&&
   current.device_generation==a->open.attempt.identity.device_generation&&
   current.open_token&&current.open_token==a->commit.open_token&&
   wr_iot_dns_activation_recovery_state()==0&&
   wr_iot_request_snapshot_expected_current(&a->admission.snapshot);
 }else if(s->phase==WR_IOT_OWNER_OFF&&a->phase==WR_IOT_RUN_STOPPED&&
          s->stop.owner==getpid()&&s->stop.active==a&&s->stop.complete&&!s->stop.busy&&
          s->stop.stop.phase==WR_IOT_STOP_COMPLETE&&!s->stop.stop.guard&&
          !a->admission.snapshot.active&&!a->admission.snapshot.token&&
          !s->stop.stop.disable.services.settings.active&&
          !s->stop.stop.disable.services.settings.token&&
          s->stop.stop.close.phase==WR_IOT_CLOSE_OWNER_RELEASED&&
          !strcmp(r->id,s->stop.id)&&r->created==s->stop.created){
  struct wr_iot_driver_closed_result closed;
  ok=wr_iot_request_disabled_current()&&!if_nametoindex("br-iot")&&
   wr_iot_bss_is_down()&&wr_iot_dns_activation_recovery_state()==0&&
   wr_iot_driver_attempt_closed(&a->open.attempt,&closed)&&
   closed.adapter_epoch==a->open.attempt.identity.adapter_epoch&&
   closed.device_generation==a->open.attempt.identity.device_generation&&
   closed.open_token&&closed.open_token==s->stop.stop.close.request.open_token&&
   closed.close_serial&&closed.close_serial==s->stop.stop.close_serial&&
   wr_iot_request_disabled_current()&&!if_nametoindex("br-iot")&&wr_iot_bss_is_down();
 }
 wr_iot_service_guard_leave(guard);return ok;
}
