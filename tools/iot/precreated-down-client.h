#ifndef WR_IOT_PRECREATED_DOWN_CLIENT_H
#define WR_IOT_PRECREATED_DOWN_CLIENT_H
#include "precreated-down-wire.h"
/* One fixed ra2 read; failure clears output. Observation, never restart lease. */
int wr_iot_driver_initial_down_read(const unsigned char *,struct wr_iot_down_result *);
#endif
