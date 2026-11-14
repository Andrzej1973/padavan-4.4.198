/* Private RC preparation for physical restart. Credentials remain in this
 * retained process context, never telemetry/mailbox output. Zero-initialize;
 * never copy a live context or discard desired settings before resume policy
 * has consumed them. Normal OFF clears the activation runner's ON request. */
#ifndef WR_IOT_RC_QUIESCE_H
#define WR_IOT_RC_QUIESCE_H
#include <sys/types.h>
#include "control-record.h"
#include "driver-api-wire.h"
struct wr_iot_rc_quiesce {
 pid_t owner;
 int active,complete,busy,resume_needed;
 char id[33];unsigned long long created;
 struct wr_iot_request desired;
};
/* Begins normal owned OFF only for a freshly observed ACTIVE backend, or
 * accepts an already owned/fresh OFF without inventing a prior ON request.
 * Caller retains shutdown/service admission across all continuation calls. */
int wr_iot_rc_quiesce_begin(struct wr_iot_rc_quiesce *,const struct wr_iot_control_request *);
/* One existing OFF recovery step, followed by fresh CLOSE observation when
 * complete. Does not ARM, stop Main or authorize adapter reset/reopen. */
int wr_iot_rc_quiesce_advance(struct wr_iot_rc_quiesce *,struct wr_iot_driver_closed_result *);
#endif
