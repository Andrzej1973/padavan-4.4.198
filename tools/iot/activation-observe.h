#ifndef WR_IOT_ACTIVATION_OBSERVE_H
#define WR_IOT_ACTIVATION_OBSERVE_H
#include "activation-owner.h"
/* Fresh configuration/service observation, never RF/client acceptance. Caller
 * supplies the retained RC owner; missing or foreign owners cannot be rebuilt
 * from mailbox records. This does not progress/repair an operation. */
int wr_iot_activation_owner_observed(const struct wr_iot_activation_owner *,
 const struct wr_iot_control_result *);
/* Obtain a fresh released CLOSE identity only from the retained OFF owner.
 * Configuration, isolation and service observation remain required. The output
 * is a software CLOSE receipt for ARM admission, not physical-stop permission. */
int wr_iot_activation_owner_closed(const struct wr_iot_activation_owner *,
 const struct wr_iot_control_result *,struct wr_iot_driver_closed_result *);
#endif
