#include <unistd.h>
#include "start-network.h"
#include "driver-api-client.h"
#include "service-guard.h"
#include "rc-shutdown-admission.h"
#include "bridge.h"
#include "network-check.h"
#include "request-stage.h"
#include "quarantine.h"
#include "dns-activation.h"
int wr_iot_start_network_step(struct wr_iot_start_network *s,
 struct wr_iot_start_admission *owner,const struct wr_iot_request *request,
 const unsigned char *nonce)
{
 struct wr_iot_idle_result current;int fd,ok=0;
 if(!s||!owner||!request||s->phase<WR_IOT_NET_BRIDGE||s->phase>WR_IOT_NET_READY||
    !owner->admitted||!owner->mutation_started||!owner->staged||
    !owner->snapshot.active||owner->snapshot.owner!=getpid()||owner->snapshot.token!=1||
    owner->snapshot.recovering||owner->snapshot.disabling)return 0;
 if(!wr_iot_rc_shutdown.active||wr_iot_rc_shutdown.pending)goto failed;
 fd=wr_iot_service_guard_dup();if(fd<0)goto failed;
 if(close(fd)||!wr_iot_driver_initial_idle_read(nonce,&current)||
    current.epoch!=owner->idle.epoch||current.generation!=owner->idle.generation||
    current.serial<=owner->idle.serial||wr_iot_rc_shutdown.pending)goto failed;
 owner->idle=current;
 if(!wr_iot_bss_is_down())goto failed;
 if(!wr_iot_request_prepared_matches(request,
    s->phase>WR_IOT_NET_ENABLE,s->phase==WR_IOT_NET_READY))goto failed;
 if(s->phase<WR_IOT_NET_READY)s->attempted|=1U<<(unsigned int)s->phase;
 switch(s->phase){
 case WR_IOT_NET_BRIDGE:
  ok=wr_iot_network_check(request->gateway,request->mask,request->first,request->last)&&
   wr_iot_bridge_prepare(request->gateway,request->mask,request->first,request->last,NULL,0);break;
 case WR_IOT_NET_QUARANTINE:ok=wr_iot_quarantine_apply();break;
 case WR_IOT_NET_ATTACH:ok=wr_iot_bridge_attach();break;
 case WR_IOT_NET_UP:ok=wr_iot_bridge_set_up(1);break;
 case WR_IOT_NET_ENABLE:ok=wr_iot_request_network_enable(request);break;
 case WR_IOT_NET_DNS:ok=wr_iot_dns_activation_prepare()==0;break;
 case WR_IOT_NET_POLICY:ok=wr_iot_policy_enable_current();break;
 case WR_IOT_NET_READY:
  if(wr_iot_request_stage_matches(request)&&
     wr_iot_network_services_ready(request->gateway)&&wr_iot_active_filter_ready_current())return 1;
  goto failed;
 default:return 0;
 }
 if(!ok||wr_iot_rc_shutdown.pending)goto failed;
 s->phase++;return 0;
failed:
 s->phase=WR_IOT_NET_RECOVERY;return 0;
}
