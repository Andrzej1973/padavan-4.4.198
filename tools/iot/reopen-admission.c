#include <string.h>
#include <unistd.h>
#include <net/if.h>
#include "reopen-admission.h"
#include "service-guard.h"
#include "request-snapshot.h"
#include "bridge.h"
#include "dns-activation.h"
int wr_iot_reopen_closed_current(const struct wr_iot_start_runner *a,
 const struct wr_iot_active_stop *stop)
{
 struct wr_iot_driver_closed_result closed;int fd;
 if(!a||!stop||a->owner!=getpid()||a->busy||a->phase!=WR_IOT_RUN_STOPPED||
    stop->owner!=getpid()||stop->active!=a||stop->busy||!stop->complete||
    stop->stop.owner!=getpid()||stop->stop.guard||
    stop->stop.phase!=WR_IOT_STOP_COMPLETE||
    stop->stop.close.phase!=WR_IOT_CLOSE_OWNER_RELEASED||
    a->admission.snapshot.active||a->admission.snapshot.token||
    stop->stop.disable.services.settings.active||stop->stop.disable.services.settings.token||
    !stop->stop.close_serial||!stop->stop.close.request.open_token||
    !a->open.attempt.identity.adapter_epoch||!a->open.attempt.identity.device_generation||
    stop->stop.attempt.identity.adapter_epoch!=a->open.attempt.identity.adapter_epoch||
    stop->stop.attempt.identity.device_generation!=a->open.attempt.identity.device_generation||
    memcmp(stop->stop.attempt.request_id,a->open.attempt.request_id,sizeof(a->open.attempt.request_id)))return 0;
 fd=wr_iot_service_guard_dup();if(fd<0)return 0;if(close(fd))return 0;
 return wr_iot_request_disabled_current()&&!if_nametoindex("br-iot")&&
  wr_iot_bss_is_down()&&wr_iot_dns_activation_recovery_state()==0&&
  wr_iot_driver_attempt_closed(&a->open.attempt,&closed)&&
  closed.adapter_epoch==a->open.attempt.identity.adapter_epoch&&
  closed.device_generation==a->open.attempt.identity.device_generation&&
  closed.open_token==stop->stop.close.request.open_token&&
  closed.close_serial==stop->stop.close_serial&&
  wr_iot_request_disabled_current()&&!if_nametoindex("br-iot")&&wr_iot_bss_is_down();
}

int wr_iot_reopen_witness_take(struct wr_iot_reopen_witness *out,
 const struct wr_iot_start_runner *a,const struct wr_iot_active_stop *stop)
{
 struct wr_iot_reopen_witness candidate={0};
 if(!out||out->owner||out->valid||out->submitted||
    !wr_iot_reopen_closed_current(a,stop))return 0;
 candidate.owner=getpid();candidate.attempt=a->open.attempt;
 candidate.open_token=stop->stop.close.request.open_token;
 candidate.close_serial=stop->stop.close_serial;candidate.valid=1;
 *out=candidate;return 1;
}
int wr_iot_reopen_witness_current(const struct wr_iot_reopen_witness *s)
{
 struct wr_iot_driver_closed_result current;int fd;unsigned i,nonzero=0;
 if(!s||s->owner!=getpid()||!s->valid||s->submitted||!s->open_token||!s->close_serial||
    !s->attempt.identity.adapter_epoch||!s->attempt.identity.device_generation)return 0;
 for(i=0;i<sizeof(s->attempt.request_id);i++)nonzero|=s->attempt.request_id[i];
 if(!nonzero)return 0;
 fd=wr_iot_service_guard_dup();if(fd<0)return 0;if(close(fd))return 0;
 return wr_iot_bss_is_down()&&wr_iot_driver_attempt_closed(&s->attempt,&current)&&
  current.adapter_epoch==s->attempt.identity.adapter_epoch&&
  current.device_generation==s->attempt.identity.device_generation&&
  current.open_token==s->open_token&&current.close_serial==s->close_serial&&
  wr_iot_bss_is_down();
}

int wr_iot_reopen_recovered_witness_take(struct wr_iot_reopen_witness *out,
 const struct wr_iot_start_runner *a)
{
 struct wr_iot_reopen_witness candidate={0};
 if(!out||out->owner||out->valid||out->submitted||!a||a->owner!=getpid()||
    a->busy||a->phase!=WR_IOT_RUN_REJECTED||
    a->admission.snapshot.active||a->admission.snapshot.token||
    a->rollback.owner!=getpid()||a->rollback.phase!=WR_IOT_ROLL_DONE||
    a->open.owner!=getpid()||
    (a->open.phase!=WR_IOT_OPEN_CONFIRMED&&a->open.phase!=WR_IOT_OPEN_RECOVERY)||
    a->close.owner!=getpid()||a->close.close.phase!=WR_IOT_CLOSE_OWNER_RELEASED||
    a->close.attempt.identity.adapter_epoch!=a->open.attempt.identity.adapter_epoch||
    a->close.attempt.identity.device_generation!=a->open.attempt.identity.device_generation||
    memcmp(a->close.attempt.request_id,a->open.attempt.request_id,sizeof(a->open.attempt.request_id))||
    a->close.close.request.adapter_epoch!=a->open.attempt.identity.adapter_epoch||
    a->close.close.request.device_generation!=a->open.attempt.identity.device_generation||
    memcmp(a->close.close.request.open_request_id,a->open.attempt.request_id,sizeof(a->open.attempt.request_id))||
    !a->close.close_serial||!a->close.close.request.open_token)return 0;
 candidate.owner=getpid();candidate.attempt=a->open.attempt;
 candidate.open_token=a->close.close.request.open_token;
 candidate.close_serial=a->close.close_serial;candidate.valid=1;
 if(!wr_iot_reopen_witness_current(&candidate)||
    !wr_iot_request_disabled_current()||if_nametoindex("br-iot")||
    !wr_iot_bss_is_down()||wr_iot_dns_activation_recovery_state()!=0||
    !wr_iot_request_disabled_current()||!wr_iot_reopen_witness_current(&candidate))return 0;
 *out=candidate;return 1;
}
