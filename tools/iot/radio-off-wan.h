#ifndef WR_IOT_RADIO_OFF_WAN_H
#define WR_IOT_RADIO_OFF_WAN_H
#include "radio-off-owner.h"
struct wr_iot_off_wan {pid_t owner;int busy,attempted,returned;struct wr_iot_radio_off_policy policy;struct wr_iot_physical_stop_request released;};
/* Caller establishes completed OFF network/service phases first. Return1 from
 * step means SDK call returned, not WAN readiness or completed OFF. */
int wr_iot_off_wan_begin(struct wr_iot_off_wan *,const struct wr_iot_radio_off_owner *);
int wr_iot_off_wan_step(struct wr_iot_off_wan *);
#endif
