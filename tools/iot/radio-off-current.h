#ifndef WR_IOT_RADIO_OFF_CURRENT_H
#define WR_IOT_RADIO_OFF_CURRENT_H
#include "physical-stop-wire.h"
/* Fresh read-only checks under a new guard. Prior RELEASE is provenance;
 * success is an observation, never a lease or permission to reopen. */
int wr_iot_radio_off_current(const struct wr_iot_physical_stop_request *);
#endif
