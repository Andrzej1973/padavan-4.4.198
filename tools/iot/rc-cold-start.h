#ifndef WR_IOT_RC_COLD_START_H
#define WR_IOT_RC_COLD_START_H
#include "cold-on-owner.h"
/* Candidate RC-private initial-start handoff, composed only into experimental RC sources.
 * 1 means backend claimed (possibly retained refusal), never ACTIVE. Parent
 * must remain at its stable address through backend stop and checked release. */
int wr_iot_rc_cold_start_begin(struct wr_iot_cold_owner *,const struct wr_iot_control_request *);
/* Advance only the existing bound START, never begin/reload another owner.
 * Return1 means one continuation call, not ACTIVE or successful submission. */
int wr_iot_rc_cold_start_progress(const struct wr_iot_cold_owner *,const struct wr_iot_control_request *);
/* Exact bound initial owner plus existing full ACTIVE observer; not APPLIED alone. */
int wr_iot_rc_cold_active_current(const struct wr_iot_cold_owner *,const struct wr_iot_control_request *);
#endif
