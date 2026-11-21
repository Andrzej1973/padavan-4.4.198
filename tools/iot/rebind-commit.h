#ifndef WR_IOT_REBIND_COMMIT_H
#define WR_IOT_REBIND_COMMIT_H
#include "start-commit.h"
#include "rebind-start.h"
/* Software commit only; actual current OPEN and network observations required.
 * DNS attempted once, uncertainty retained, snapshot suspended only after commit. */
int wr_iot_rebind_commit_step(struct wr_iot_start_commit *,struct wr_iot_rebind_start *,
 const struct wr_iot_start_network *,const struct wr_iot_rebind_open_controller *,
 const struct wr_iot_request *);
#endif
