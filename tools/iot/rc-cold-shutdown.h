#ifndef WR_IOT_RC_COLD_SHUTDOWN_H
#define WR_IOT_RC_COLD_SHUTDOWN_H
#include "cold-on-handoff.h"
#include "rc-quiesce.h"
/* Pending shutdown only: exact bound initial owner and completed owned OFF.
 * Fresh software CLOSE receipt, not RF/DMA/IRQ retirement or reopen permission. */
int wr_iot_rc_cold_shutdown_closed(const struct wr_iot_cold_owner *,const struct wr_iot_cold_handoff *,
 const struct wr_iot_rc_quiesce *,struct wr_iot_driver_closed_result *);
#endif
