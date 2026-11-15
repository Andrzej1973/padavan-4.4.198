#include <net/if.h>
#include <unistd.h>
#include "radio-off-observe.h"
#include "physical-stop-client.h"
#include "rc-shutdown-admission.h"
#include "restart-main-state.h"
#include "service-guard.h"
int wr_iot_radio_off_observed(const struct wr_iot_physical_stop_request *released)
{
 struct wr_iot_physical_stop_request query;
 struct wr_iot_physical_stop_response reply={0},checked={0};
 unsigned char wire[64];unsigned index;int token,ok=0;
 if(!wr_iot_physical_stop_request_valid(released)||released->action!=WR_STOP_RELEASE||
    !wr_iot_rc_shutdown.radio_off_owned||wr_iot_rc_shutdown.active||wr_iot_rc_shutdown.pending)return 0;
 query=*released;query.action=WR_STOP_QUERY;
 token=wr_iot_service_guard_enter(1);if(token!=1)return 0;
 index=if_nametoindex("ra0");
 if(index&&wr_iot_restart_main_down()&&
    wr_iot_physical_stop_call(&query,&reply)==WR_PHYSICAL_CALL_ACKNOWLEDGED&&
    wr_iot_physical_stop_response_encode(wire,sizeof(wire),&reply.identity,reply.identity.attempt,reply.status)&&
    wr_iot_physical_stop_response_decode(&checked,wire,sizeof(wire),&query)&&
    checked.status==WR_STOP_COMPLETE&&wr_iot_restart_main_down()&&
    if_nametoindex("ra0")==index&&wr_iot_rc_shutdown.radio_off_owned&&
    !wr_iot_rc_shutdown.active&&!wr_iot_rc_shutdown.pending)ok=1;
 wr_iot_service_guard_leave(token);return ok;
}
