#include <net/if.h>
#include <unistd.h>
#include "radio-off-current.h"
#include "rc-backend.h"
#include "rc-shutdown-admission.h"
#include "restart-main-state.h"
#include "service-guard.h"
static int same_closed(const struct wr_iot_physical_stop_request *r,
 const struct wr_iot_driver_closed_result *c)
{
 return c->adapter_epoch==r->epoch&&c->device_generation==r->generation&&
  c->open_token==r->open_token&&c->close_serial==r->closed_serial;
}
int wr_iot_radio_off_current(const struct wr_iot_physical_stop_request *released)
{
 struct wr_iot_driver_closed_result before={0},after={0};unsigned index;int token,ok=0;
 if(!wr_iot_physical_stop_request_valid(released)||released->action!=WR_STOP_RELEASE||
    !wr_iot_rc_shutdown.radio_off_owned||wr_iot_rc_shutdown.active||wr_iot_rc_shutdown.pending)return 0;
 token=wr_iot_service_guard_enter(1);if(token!=1)return 0;
 index=if_nametoindex("ra0");
 if(index&&wr_iot_rc_backend_closed(&before)&&same_closed(released,&before)&&
    wr_iot_restart_main_down()&&wr_iot_rc_backend_closed(&after)&&same_closed(released,&after)&&
    wr_iot_restart_main_down()&&if_nametoindex("ra0")==index&&
    wr_iot_rc_shutdown.radio_off_owned&&!wr_iot_rc_shutdown.active&&!wr_iot_rc_shutdown.pending)ok=1;
 wr_iot_service_guard_leave(token);return ok;
}
