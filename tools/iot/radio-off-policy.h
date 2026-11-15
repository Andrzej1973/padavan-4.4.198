#ifndef WR_IOT_RADIO_OFF_POLICY_H
#define WR_IOT_RADIO_OFF_POLICY_H
#include "restart-wan-plan.h"
/* Read-only SDK OFF policy snapshot. Does not authorize physical stop,
 * service launch, profile write, WAN dispatch or completion. */
struct wr_iot_radio_off_policy {int reload,stored_radio,auth_required;enum wr_iot_wan_followup wan;};
int wr_iot_rc_radio_off_policy(int,struct wr_iot_radio_off_policy *);
#endif
