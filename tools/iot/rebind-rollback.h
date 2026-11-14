#ifndef WR_IOT_REBIND_ROLLBACK_H
#define WR_IOT_REBIND_ROLLBACK_H
#include "start-network-rollback.h"
#include "rebind-start.h"
/* Pre-OPEN only. A possible new OPEN requires its own CLOSE before rollback. */
int wr_iot_rebind_rollback_step(struct wr_iot_start_network_rollback *,
 struct wr_iot_start_network *,struct wr_iot_rebind_start *,
 const struct wr_iot_rebind_open_controller *);
#endif
