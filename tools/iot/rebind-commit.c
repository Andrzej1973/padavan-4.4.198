#include <string.h>
#include <unistd.h>
#include "rebind-commit.h"
#include "service-guard.h"
#include "rc-shutdown-admission.h"
#include "request-stage.h"
#include "network-check.h"
#include "quarantine.h"
#include "dns-activation.h"
int wr_iot_rebind_commit_step(struct wr_iot_start_commit *s,
 struct wr_iot_rebind_start *rebind,const struct wr_iot_start_network *network,
 const struct wr_iot_rebind_open_controller *open,const struct wr_iot_request *request)
{
 struct wr_iot_start_admission *owner;
 struct wr_iot_driver_open_current_result current;int fd;
 if(!rebind||rebind->owner!=getpid())return 0;
 owner=&rebind->admission;
 if(!s||!owner||!network||!open||!request||!request->enabled||
    !wr_iot_rc_shutdown.active||wr_iot_rc_shutdown.pending||
    network->phase!=WR_IOT_NET_READY||open->phase!=WR_REBIND_OPEN_CURRENT||
    open->owner!=getpid()||!owner->admitted||!owner->staged||
    !owner->mutation_started||!owner->snapshot.active||
    owner->snapshot.owner!=getpid()||owner->snapshot.disabling||owner->snapshot.recovering||
    owner->reopened!=2||
    memcmp(open->attempt.request_id,rebind->open_id,sizeof(rebind->open_id))||
    open->attempt.identity.adapter_epoch!=rebind->identity.adapter_epoch||
    open->attempt.identity.device_generation!=rebind->identity.device_generation)return 0;
 if(s->phase==WR_IOT_COMMIT_DNS_UNCERTAIN||s->phase==WR_IOT_COMMIT_ACTIVE)return 0;
 if(s->phase!=WR_IOT_COMMIT_IDLE&&s->phase!=WR_IOT_COMMIT_DNS_COMMITTED)return 0;
 if(owner->snapshot.token!=1)return 0;
 fd=wr_iot_service_guard_dup();if(fd<0)return 0;if(close(fd))return 0;
 if(s->owner){
  if(s->owner!=getpid()||
     memcmp(s->attempt.request_id,open->attempt.request_id,sizeof(s->attempt.request_id))||
     s->attempt.identity.adapter_epoch!=open->attempt.identity.adapter_epoch||
     s->attempt.identity.device_generation!=open->attempt.identity.device_generation)return 0;
 }else if(s->phase!=WR_IOT_COMMIT_IDLE||s->open_token)return 0;
 if(!wr_iot_request_stage_matches(request)||
    !wr_iot_network_services_ready(request->gateway)||
    !wr_iot_active_filter_observed_current()||
    !wr_iot_driver_open_current_read(&open->attempt,&current)||!current.open_token||
    current.adapter_epoch!=open->attempt.identity.adapter_epoch||
    current.device_generation!=open->attempt.identity.device_generation||
    (s->open_token&&s->open_token!=current.open_token)||
    !wr_iot_request_stage_matches(request)||wr_iot_rc_shutdown.pending)return 0;
 if(!s->owner){s->owner=getpid();s->attempt=open->attempt;s->open_token=current.open_token;}
 if(s->phase==WR_IOT_COMMIT_IDLE){
  if(wr_iot_dns_activation_recovery_state()!=1)return 0;
  s->phase=WR_IOT_COMMIT_DNS_UNCERTAIN;
  if(wr_iot_dns_activation_commit())s->phase=WR_IOT_COMMIT_DNS_COMMITTED;
  return 0;
 }
 if(wr_iot_dns_activation_recovery_state()!=0||
    !wr_iot_request_snapshot_suspend(&owner->snapshot))return 0;
 s->phase=WR_IOT_COMMIT_ACTIVE;return 1;
}
