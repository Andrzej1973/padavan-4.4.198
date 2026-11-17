#include "check-config-server-unused.h"
/* Queue/owner-only fixtures inject the backend publication gate. They do not
 * implement the RC backend or claim automatic radio shutdown arming. */
#ifndef WR_IOT_CHECK_MAILBOX_ROUTE_ACTOR_H
#define WR_IOT_CHECK_MAILBOX_ROUTE_ACTOR_H
#include "rc-shutdown-admission.h"
int wr_iot_rc_backend_applied_route(const char *id,unsigned long long created){
 return wr_iot_rc_shutdown.active&&id&&wr_iot_control_id(id)&&created;
}
#endif
