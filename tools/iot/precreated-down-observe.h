#ifndef WR_IOT_PRECREATED_DOWN_OBSERVE_H
#define WR_IOT_PRECREATED_DOWN_OBSERVE_H
#include "precreated-down-client.h"
/* Caller owns active admission/config guard. Double read, no mutation or
 * future lease. Does not replace a historical owned-IoT RELEASE receipt. */
int wr_iot_initial_down_observe(const unsigned char *,struct wr_iot_down_result *);
#endif
