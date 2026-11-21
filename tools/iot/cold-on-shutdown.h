#ifndef WR_IOT_COLD_ON_SHUTDOWN_H
#define WR_IOT_COLD_ON_SHUTDOWN_H
#include "cold-on-owner.h"
/* Private prehandoff shutdown only. Caller owns sole stable cold root and no
 * submitted backend handoff. One owned Guest recovery step per call; no Main
 * mutation or profile rollback. Failed proof/unmask retains root and guard. */
int wr_iot_cold_prehandoff_shutdown(struct wr_iot_cold_owner *);
#endif
