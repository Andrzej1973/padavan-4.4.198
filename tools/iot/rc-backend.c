#include "control-channel.h"
#include "rc-backend.h"
#include "activation-observe.h"
#include "service-guard.h"
#include "rc-shutdown-admission.h"
static struct wr_iot_activation_owner backend;
enum wr_iot_result_state wr_iot_activation_execute(const struct wr_iot_control_request *request)
{
 struct wr_iot_rc_mode mode={0};enum wr_iot_result_state result;
 int guard;
 if(!request)return WR_IOT_RESULT_REJECTED;
 if(!wr_iot_rc_shutdown.active)return WR_IOT_RESULT_RECOVERY;
 /* Never let a failed new mode observation turn an already retained recovery
  * into a terminal rejection. Only continuation can advance that owner. */
 if(backend.phase==WR_IOT_OWNER_START||backend.phase==WR_IOT_OWNER_STOP)
  return WR_IOT_RESULT_RECOVERY;
 guard=wr_iot_service_guard_enter(1);if(guard!=1)return WR_IOT_RESULT_REJECTED;
 if(request->request.enabled==1&&wr_iot_rc_mode_read(&mode)!=1){
  wr_iot_service_guard_leave(guard);return WR_IOT_RESULT_REJECTED;
 }
 result=wr_iot_activation_owner_execute(&backend,request,mode.router,mode.radio,mode.mode);
 wr_iot_service_guard_leave(guard);return result;
}
enum wr_iot_result_state wr_iot_activation_continue(const char *id,unsigned long long created)
{
 return wr_iot_activation_owner_continue(&backend,id,created);
}
int wr_iot_rc_backend_observed(const struct wr_iot_control_result *result)
{
 return wr_iot_activation_owner_observed(&backend,result);
}
