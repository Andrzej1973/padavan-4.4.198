/* Post-OPEN rebind recovery: CLOSE the exact new-epoch attempt before any
 * network teardown. Caller retains physical restart ownership and snapshot. */
#ifndef WR_IOT_REBIND_CLOSE_H
#define WR_IOT_REBIND_CLOSE_H
#include "rebind-start.h"
#include "start-close.h"
int wr_iot_rebind_close_step(struct wr_iot_start_close *,
 const struct wr_iot_rebind_start *,const struct wr_iot_rebind_open_controller *);
#endif
