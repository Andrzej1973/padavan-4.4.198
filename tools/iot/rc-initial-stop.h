#ifndef WR_IOT_RC_INITIAL_STOP_H
#define WR_IOT_RC_INITIAL_STOP_H
#include "physical-initial-session.h"
#include "restart-auth-stop.h"
#include "initial-shutdown-owner.h"
/* Embedded in the RC physical owner. Outer service/signal admission must span
 * the whole operation and terminal consumption. Never copy a live owner. */
struct wr_iot_rc_initial_stop {
 pid_t owner;int busy,result;
 const struct wr_iot_initial_shutdown_owner *shutdown;
 unsigned aux_next;
 unsigned char nonce[16];
 struct wr_iot_auth_stop auth;
 struct wr_iot_initial_physical_session session;
};
int wr_iot_rc_initial_stop_begin(struct wr_iot_rc_initial_stop *,const unsigned char *);
int wr_iot_rc_initial_stop_begin_shutdown(struct wr_iot_rc_initial_stop *,const unsigned char *,const struct wr_iot_initial_shutdown_owner *);
int wr_iot_rc_initial_stop_step(struct wr_iot_rc_initial_stop *);
/* Typed RELEASE only; not a legacy OPEN/CLOSE tuple or permission to reopen. */
int wr_iot_rc_initial_stop_released(const struct wr_iot_rc_initial_stop *,
 struct wr_iot_physical_initial_request *);
#endif
