#ifndef WR_IOT_ACTIVATION_OBSERVE_H
#define WR_IOT_ACTIVATION_OBSERVE_H
#include "activation-owner.h"
/* Fresh configuration/service observation, never RF/client acceptance. Caller
 * supplies the retained RC owner; missing or foreign owners cannot be rebuilt
 * from mailbox records. This does not progress/repair an operation. */
int wr_iot_activation_owner_observed(const struct wr_iot_activation_owner *,
 const struct wr_iot_control_result *);
#endif
