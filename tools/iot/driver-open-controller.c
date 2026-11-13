#include <string.h>
#include <unistd.h>
#include "driver-open-controller.h"
#include "request-stage.h"
#include "service-guard.h"
#include "network-check.h"
#include "bridge.h"
#include "quarantine.h"
static int open_guard_valid(void)
{
 int fd=wr_iot_service_guard_dup();return fd>=0&&close(fd)==0;
}
int wr_iot_open_controller_submit(struct wr_iot_open_controller *s,const char *id,
 const struct wr_iot_request *request)
{
 enum wr_iot_driver_submit_result result;
 if(!s||s->phase!=WR_IOT_OPEN_IDLE||s->owner||!request||!open_guard_valid()||
    !wr_iot_request_stage_matches(request)||!wr_iot_bss_is_down()||
    !wr_iot_network_check(request->gateway,request->mask,request->first,request->last)||
    !wr_iot_bridge_address_matches(request->gateway,request->mask)||
    !wr_iot_network_services_ready(request->gateway)||
    !wr_iot_active_filter_ready_current()||!wr_iot_request_stage_matches(request))return 0;
 s->owner=getpid();s->phase=WR_IOT_OPEN_SUBMITTING;
 result=wr_iot_driver_open_requested_tracked(id,request,&s->attempt);
 if(result==WR_IOT_DRIVER_NOT_SUBMITTED){s->phase=WR_IOT_OPEN_NOT_SUBMITTED;return 0;}
 s->phase=WR_IOT_OPEN_RECOVERY;
 if(result!=WR_IOT_DRIVER_OPEN_COMPLETED||!open_guard_valid()||
    !wr_iot_active_filter_observed_current()||!wr_iot_request_stage_matches(request))return 0;
 s->phase=WR_IOT_OPEN_CONFIRMED;return 1;
}
int wr_iot_open_controller_recovery_read(const struct wr_iot_open_controller *s,
 struct wr_iot_driver_open_recovery_result *out)
{
 if(!out)return 0;
 memset(out,0,sizeof(*out));
 if(!s||s->owner!=getpid()||
    (s->phase!=WR_IOT_OPEN_CONFIRMED&&s->phase!=WR_IOT_OPEN_RECOVERY)||
    !open_guard_valid())return 0;
 return wr_iot_driver_open_recovery_read(&s->attempt,out);
}
