#ifndef WR_IOT_RADIO_OFF_STATE_H
#define WR_IOT_RADIO_OFF_STATE_H
#include "radio-off-policy.h"
#include "physical-stop-wire.h"
/* Caller owns service guard and records one attempt before invocation.
 * Partial writes/readback refusal are uncertainty; never replay implicitly.
 * Temporary SDK state only: no flash commit or RF command. */
int wr_iot_rc_radio_off_state(const struct wr_iot_radio_off_policy *,const struct wr_iot_physical_stop_request *);
#endif
