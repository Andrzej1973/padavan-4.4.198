#ifndef WR_IOT_COLD_ON_PREHANDOFF_H
#define WR_IOT_COLD_ON_PREHANDOFF_H
#include "cold-on-owner.h"
/* Pending shutdown only; no profile restore, Main reset, OPEN or cleanup.
 * Caller must drain its submitted Guest UP before this proof can pass. */
int wr_iot_cold_prehandoff_shutdown_current(struct wr_iot_cold_owner *);
/* RC-private backend observation, no cold initial start may have been claimed. */
int wr_iot_rc_cold_never_started(const struct wr_iot_cold_owner *);
#endif
