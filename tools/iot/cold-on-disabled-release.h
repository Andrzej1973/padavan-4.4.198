#ifndef WR_IOT_COLD_ON_DISABLED_RELEASE_H
#define WR_IOT_COLD_ON_DISABLED_RELEASE_H
#include "cold-on-disabled.h"
#include "cold-on-policy.h"
#include "restart-profile-receipt.h"
#include "restart-wan-followup.h"
/* Distinct never-opened OFF release preparation: no ACTIVE/OPEN/RELEASE tuple.
 * Stable context retains all parent resources on refusal. No cleanup yet. */
struct wr_iot_cold_disabled_release {
 pid_t owner;int busy;struct wr_iot_cold_disabled *disabled;
 struct wr_iot_cold_owner *parent;struct wr_iot_driver_identity identity;
 char id[33];unsigned long long created;
 struct wr_iot_cold_policy policy;struct wr_iot_restart_profile_receipt profile;
 struct wr_iot_wan_followup_state wan;
};
int wr_iot_cold_disabled_release_begin(struct wr_iot_cold_disabled_release *,struct wr_iot_cold_disabled *);
int wr_iot_cold_disabled_release_current(struct wr_iot_cold_disabled_release *);
#endif
