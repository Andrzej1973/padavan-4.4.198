#ifndef WR_IOT_RADIO_ON_ROLLBACK_STATE_H
#define WR_IOT_RADIO_ON_ROLLBACK_STATE_H
#include "physical-stop-wire.h"
/* Pre-UP caller only, restored baseline and original OFF receipt required.
 * Sets only RAM mlme_radio_rt0; never rewinds watchdog reload event or commits.
 * Caller marks attempt before invocation and retains any uncertainty. */
int wr_iot_rc_radio_on_rollback_state(const struct wr_iot_physical_stop_request *);
#endif
