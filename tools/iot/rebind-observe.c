#define _GNU_SOURCE
#include <string.h>
#include <unistd.h>
#include <net/if.h>
#include "rebind-observe.h"
#include "service-guard.h"
#include "request-stage.h"
#include "network-check.h"
#include "bridge.h"
#include "quarantine.h"
#include "dns-activation.h"
static int result_valid(const struct wr_iot_control_result *r)
{return r&&r->state==WR_IOT_RESULT_APPLIED&&r->created&&
 memchr(r->id,0,sizeof(r->id))&&wr_iot_control_id(r->id);}
int wr_iot_rebind_active_observed(const struct wr_iot_rebind_runner *s,
 const struct wr_iot_control_result *r)
{
 struct wr_iot_driver_open_current_result current={0};
 const struct wr_iot_request *request;int guard,ok;
 if(!s||!result_valid(r)||s->owner!=getpid()||s->busy||
    s->phase!=WR_IOT_RUN_ACTIVE||s->commit.phase!=WR_IOT_COMMIT_ACTIVE||
    s->commit.owner!=getpid()||s->open.owner!=getpid()||s->open.busy||
    s->open.phase!=WR_REBIND_OPEN_CURRENT||s->start.owner!=getpid()||
    s->start.admission.reopened!=2||s->network.phase!=WR_IOT_NET_READY||
    !memchr(s->input.id,0,sizeof(s->input.id))||
    strcmp(r->id,s->input.id)||r->created!=s->input.created||
    memcmp(s->open.attempt.request_id,s->start.open_id,16)||
    memcmp(s->commit.attempt.request_id,s->start.open_id,16)||
    s->open.attempt.identity.adapter_epoch!=s->start.identity.adapter_epoch||
    s->open.attempt.identity.device_generation!=s->start.identity.device_generation||
    s->commit.attempt.identity.adapter_epoch!=s->start.identity.adapter_epoch||
    s->commit.attempt.identity.device_generation!=s->start.identity.device_generation)return 0;
 guard=wr_iot_service_guard_enter(1);if(guard!=1)return 0;
 request=&s->input.request;
 ok=request->enabled==1&&wr_iot_request_snapshot_expected_current(&s->start.admission.snapshot)&&
  wr_iot_request_stage_matches(request)&&
  wr_iot_network_check(request->gateway,request->mask,request->first,request->last)&&
  wr_iot_bridge_address_matches(request->gateway,request->mask)&&
  wr_iot_network_services_ready(request->gateway)&&wr_iot_active_filter_observed_current()&&
  wr_iot_driver_open_current_read(&s->open.attempt,&current)&&
  current.adapter_epoch==s->open.attempt.identity.adapter_epoch&&
  current.device_generation==s->open.attempt.identity.device_generation&&
  current.open_token&&current.open_token==s->commit.open_token&&
  wr_iot_dns_activation_recovery_state()==0&&
  wr_iot_request_snapshot_expected_current(&s->start.admission.snapshot);
 wr_iot_service_guard_leave(guard);return ok;
}
int wr_iot_rebind_off_observed(const struct wr_iot_rebind_runner *s,
 const struct wr_iot_rebind_active_stop *stop,const struct wr_iot_control_result *r)
{
 struct wr_iot_driver_closed_result closed={0};int guard,ok;
 if(!s||!stop||!result_valid(r)||s->owner!=getpid()||s->busy||
    s->phase!=WR_IOT_RUN_STOPPED||stop->owner!=getpid()||stop->active!=s||
    !stop->complete||stop->busy||stop->stop.phase!=WR_IOT_STOP_COMPLETE||stop->stop.guard||
    s->start.admission.snapshot.active||s->start.admission.snapshot.token||
    stop->stop.disable.services.settings.active||stop->stop.disable.services.settings.token||
    stop->stop.close.phase!=WR_IOT_CLOSE_OWNER_RELEASED||
    !memchr(stop->id,0,sizeof(stop->id))||strcmp(r->id,stop->id)||r->created!=stop->created)return 0;
 guard=wr_iot_service_guard_enter(1);if(guard!=1)return 0;
 ok=wr_iot_request_disabled_current()&&!if_nametoindex("br-iot")&&
  wr_iot_bss_is_down()&&wr_iot_dns_activation_recovery_state()==0&&
  wr_iot_driver_attempt_closed(&s->open.attempt,&closed)&&
  closed.adapter_epoch==s->open.attempt.identity.adapter_epoch&&
  closed.device_generation==s->open.attempt.identity.device_generation&&
  closed.open_token&&closed.open_token==stop->stop.close.request.open_token&&
  closed.close_serial&&closed.close_serial==stop->stop.close_serial&&
  wr_iot_request_disabled_current()&&!if_nametoindex("br-iot")&&wr_iot_bss_is_down();
 wr_iot_service_guard_leave(guard);return ok;
}
int wr_iot_rebind_off_closed(const struct wr_iot_rebind_runner *s,
 const struct wr_iot_rebind_active_stop *stop,const struct wr_iot_control_result *r,
 struct wr_iot_driver_closed_result *out)
{
 struct wr_iot_driver_closed_result closed={0};int guard,ok=0;
 if(!out)return 0;
 memset(out,0,sizeof(*out));
 if(!s||!stop)return 0;
 guard=wr_iot_service_guard_enter(1);if(guard!=1)return 0;
 if(wr_iot_rebind_off_observed(s,stop,r)&&
    wr_iot_driver_attempt_closed(&s->open.attempt,&closed)&&
    closed.adapter_epoch==s->open.attempt.identity.adapter_epoch&&
    closed.device_generation==s->open.attempt.identity.device_generation&&
    closed.open_token&&closed.open_token==stop->stop.close.request.open_token&&
    closed.close_serial&&closed.close_serial==stop->stop.close_serial){*out=closed;ok=1;}
 wr_iot_service_guard_leave(guard);return ok;
}
