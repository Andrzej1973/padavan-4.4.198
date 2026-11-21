#define _GNU_SOURCE
#include <unistd.h>
#include "cold-on-policy.h"
#include "service-guard.h"
#include "radio-on-aux.h"
#include "restart-main-bridge.h"
#include "restart-guest-policy.h"
#include "restart-guest-bridge.h"
#include "restart-guest-isolation.h"
#include "restart-guest-up.h"
#include "restart-multicast.h"
int wr_iot_cold_policy_current(const struct wr_iot_cold_policy *s)
{
 struct wr_iot_restart_service_policy service;struct wr_iot_multicast_policy mc;
 int guest,isolate,state,fd;
 if(!s||s->owner!=getpid()||(s->guest!=0&&s->guest!=1)||(s->isolate!=0&&s->isolate!=1))return 0;
 fd=wr_iot_service_guard_dup();if(fd<0)return 0;if(close(fd))return 0;
 return wr_iot_on_aux_down_current()&&wr_iot_restart_main_bridge_current()&&
  wr_iot_rc_restart_guest_policy(&guest)&&guest==s->guest&&
  wr_iot_rc_restart_guest_isolation_policy(&isolate)&&isolate==s->isolate&&
  wr_iot_restart_guest_admin_state(&state)&&state==guest&&
  (!guest||(wr_iot_restart_guest_bridge_current()&&wr_iot_restart_guest_isolation_current(isolate)))&&
  wr_iot_rc_restart_service_policy(&service)&&service.enterprise==s->services.enterprise&&
  service.kick_rssi==s->services.kick_rssi&&service.assoc_rssi==s->services.assoc_rssi&&
  wr_iot_rc_restart_auth_process_current(&service)&&
  wr_iot_rc_restart_multicast_policy(&mc)&&mc.required==s->multicast.required&&
  mc.enabled==s->multicast.enabled&&mc.guest==s->multicast.guest&&
  (!mc.required||(wr_iot_restart_multicast_current(0,mc.enabled)&&
   (!mc.guest||wr_iot_restart_multicast_current(1,mc.enabled))));
}
