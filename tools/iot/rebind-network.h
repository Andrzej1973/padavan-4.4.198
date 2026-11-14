#ifndef WR_IOT_REBIND_NETWORK_H
#define WR_IOT_REBIND_NETWORK_H
#include "start-network.h"
#include "rebind-start.h"
/* Existing seven network operations, gated by current rebind observation.
 * Failure retains snapshot and RECOVERY, never retries or rolls back implicitly. */
int wr_iot_rebind_network_step(struct wr_iot_start_network *,
 struct wr_iot_rebind_start *,const struct wr_iot_request *);
#endif
