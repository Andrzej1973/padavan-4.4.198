#ifndef WR_IOT_CONFIG_SAVE_SERVER_H
#define WR_IOT_CONFIG_SAVE_SERVER_H
#include "control-channel.h"
/* Explicit startup binding only; no HTTP route or implicit constructor. */
int wr_iot_rc_save_backend_install(void);
int wr_iot_rc_save_observed(const struct wr_iot_control_result *);
#endif
