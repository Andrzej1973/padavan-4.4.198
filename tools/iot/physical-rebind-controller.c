#include <string.h>
#include <unistd.h>
#include "physical-rebind-controller.h"
#include "service-guard.h"
#include "rc-shutdown-admission.h"
static int rebind_guard(void)
{
 int fd;
 if(!wr_iot_rc_shutdown.active)return 0;
 fd=wr_iot_service_guard_dup();return fd>=0&&close(fd)==0;
}
int wr_iot_rebind_open_submit(struct wr_iot_rebind_open_controller *s,
 const struct wr_iot_physical_rebind_request *request)
{
 enum wr_iot_rebind_call_result result;unsigned i;
 if(!s||!request||s->owner||s->busy||s->phase!=WR_REBIND_OPEN_IDLE||
    request->operation!=WR_REBIND_OPEN||!rebind_guard())return 0;
 s->owner=getpid();s->busy=1;s->phase=WR_REBIND_OPEN_RETAINED;
 s->attempt.identity.adapter_epoch=request->open.adapter_epoch;
 s->attempt.identity.device_generation=request->open.device_generation;
 for(i=0;i<16;i++)s->attempt.request_id[i]=request->open.request_id[i];
 result=wr_iot_physical_rebind_call(request);
 if(result==WR_REBIND_NOT_SUBMITTED){
  memset(&s->attempt,0,sizeof(s->attempt));s->phase=WR_REBIND_OPEN_NOT_SUBMITTED;
 }
 s->busy=0;
 return result==WR_REBIND_IOCTL_RETURNED;
}
int wr_iot_rebind_open_current(struct wr_iot_rebind_open_controller *s,
 struct wr_iot_driver_open_current_result *out)
{
 struct wr_iot_driver_open_current_result current={0};int ok=0;
 if(!out)return 0;
 memset(out,0,sizeof(*out));
 if(!s||s->owner!=getpid()||s->busy||
    (s->phase!=WR_REBIND_OPEN_RETAINED&&s->phase!=WR_REBIND_OPEN_CURRENT)||!rebind_guard())return 0;
 s->busy=1;
 if(wr_iot_driver_open_current_read(&s->attempt,&current)&&current.open_token&&
    current.adapter_epoch==s->attempt.identity.adapter_epoch&&
    current.device_generation==s->attempt.identity.device_generation){
  *out=current;s->phase=WR_REBIND_OPEN_CURRENT;ok=1;
 }
 s->busy=0;return ok;
}
int wr_iot_rebind_open_recovery(const struct wr_iot_rebind_open_controller *s,
 struct wr_iot_driver_open_recovery_result *out)
{
 struct wr_iot_driver_open_recovery_result observed={0};
 if(!out)return 0;
 memset(out,0,sizeof(*out));
 if(!s||s->owner!=getpid()||s->busy||
    (s->phase!=WR_REBIND_OPEN_RETAINED&&s->phase!=WR_REBIND_OPEN_CURRENT)||!rebind_guard())return 0;
 if(!wr_iot_driver_open_recovery_read(&s->attempt,&observed)||!observed.open_token||
    observed.adapter_epoch!=s->attempt.identity.adapter_epoch||
    observed.device_generation!=s->attempt.identity.device_generation)return 0;
 *out=observed;return 1;
}
