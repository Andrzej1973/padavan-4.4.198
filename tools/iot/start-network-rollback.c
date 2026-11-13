#include <string.h>
#include <unistd.h>
#include <net/if.h>
#include "start-network-rollback.h"
#include "driver-api-client.h"
#include "service-guard.h"
#include "rc-shutdown-admission.h"
#include "bridge.h"
#include "dns-activation.h"
int wr_iot_start_network_rollback_step(struct wr_iot_start_network_rollback *s,
 struct wr_iot_start_network *network,struct wr_iot_start_admission *owner,
 const struct wr_iot_open_controller *open,const unsigned char *nonce)
{
 struct wr_iot_idle_result current;int fd,dns;
 if(!s||!network||!owner||!open||network->phase!=WR_IOT_NET_RECOVERY||
    (open->phase!=WR_IOT_OPEN_IDLE&&open->phase!=WR_IOT_OPEN_NOT_SUBMITTED))return 0;
 /* These phases carry no driver attempt. Never erase an unexpected identity
  * just because a phase claims no OPEN was submitted. */
 {unsigned int i;for(i=0;i<16;i++)if(open->attempt.request_id[i])return 0;}
 if(open->attempt.identity.adapter_epoch||open->attempt.identity.device_generation)return 0;
 if(s->owner&&s->owner!=getpid())return 0;
 if(!s->owner){
  if(s->phase!=WR_IOT_ROLL_BRIDGE_DOWN)return 0;
  s->owner=getpid();
 }
 if(s->phase==WR_IOT_ROLL_DONE)return !owner->snapshot.active;
 if(s->phase<WR_IOT_ROLL_BRIDGE_DOWN||s->phase>WR_IOT_ROLL_FINISH||
    !owner->admitted||!owner->mutation_started||!owner->snapshot.active||
    owner->snapshot.owner!=getpid()||owner->snapshot.token!=1||
    !wr_iot_rc_shutdown.active)return 0;
 fd=wr_iot_service_guard_dup();if(fd<0)return 0;
 if(close(fd)||!wr_iot_driver_initial_idle_read(nonce,&current)||
    current.epoch!=owner->idle.epoch||current.generation!=owner->idle.generation||
    current.serial<=owner->idle.serial||!wr_iot_bss_is_down())return 0;
 owner->idle=current;
 switch(s->phase){
 case WR_IOT_ROLL_BRIDGE_DOWN:if(!wr_iot_bridge_set_up(0))return 0;break;
 case WR_IOT_ROLL_DETACH:if(!wr_iot_bridge_detach())return 0;break;
 case WR_IOT_ROLL_REMOVE:if(!wr_iot_bridge_remove())return 0;break;
 case WR_IOT_ROLL_DNS:
  dns=wr_iot_dns_activation_recovery_state();
  if(dns<0)return 0;
  if(dns==1){
   if(!(network->attempted&(1U<<WR_IOT_NET_DNS)))return 0;
   if(!wr_iot_dns_activation_abort())return 0;
  }
  if(wr_iot_dns_activation_recovery_state()!=0)return 0;
  break;
 case WR_IOT_ROLL_SETTINGS:
  if(!wr_iot_request_snapshot_restore(&owner->snapshot))return 0;
  break;
 case WR_IOT_ROLL_OBSERVE:
  if(if_nametoindex("br-iot")||wr_iot_dns_activation_recovery_state()!=0||
     !wr_iot_request_snapshot_restored_current(&owner->snapshot))return 0;
  break;
 case WR_IOT_ROLL_FINISH:
  if(if_nametoindex("br-iot")||wr_iot_dns_activation_recovery_state()!=0||
     !wr_iot_request_snapshot_restored_current(&owner->snapshot)||
     !wr_iot_request_snapshot_finish(&owner->snapshot))return 0;
  s->phase=WR_IOT_ROLL_DONE;return 1;
 default:return 0;
 }
 s->phase++;return 0;
}
