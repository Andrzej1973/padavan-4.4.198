#ifndef WR_IOT_RC_COLD_SHUTDOWN_H
#define WR_IOT_RC_COLD_SHUTDOWN_H
#include "cold-on-handoff.h"
#include "rc-quiesce.h"
/* Pending shutdown only: exact bound initial owner and completed owned OFF.
 * Fresh software CLOSE receipt, not RF/DMA/IRQ retirement or reopen permission. */
int wr_iot_rc_cold_shutdown_closed(const struct wr_iot_cold_owner *,const struct wr_iot_cold_handoff *,
 const struct wr_iot_rc_quiesce *,struct wr_iot_driver_closed_result *);
/* Distinct completed pre-OPEN rejection: no CLOSE token/serial is invented. */
int wr_iot_rc_cold_shutdown_rejected(const struct wr_iot_cold_owner *,const struct wr_iot_cold_handoff *);
/* Advance the bound existing startup once under pending shutdown. Return1
 * only if it is now ACTIVE; never calls a new startup begin. */
int wr_iot_rc_cold_shutdown_advance(const struct wr_iot_cold_owner *,const struct wr_iot_cold_handoff *);
/* One existing normal-OFF admission, with a fresh credential-free OFF input. */
int wr_iot_rc_cold_shutdown_off_begin(const struct wr_iot_cold_owner *,const struct wr_iot_cold_handoff *,
 struct wr_iot_rc_quiesce *,const struct wr_iot_control_request *);
#endif
