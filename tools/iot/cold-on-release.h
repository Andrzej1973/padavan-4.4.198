#ifndef WR_IOT_COLD_ON_RELEASE_H
#define WR_IOT_COLD_ON_RELEASE_H
#include "cold-on-handoff.h"
#include "restart-profile-receipt.h"
#include "restart-wan-followup.h"
/* Private stable release preparation. Captures only nonsecret file identity
 * and WAN intent; never frees parent, releases guard or submits WAN. */
struct wr_iot_cold_release {
 pid_t owner;int busy;
 struct wr_iot_cold_handoff *handoff;
 struct wr_iot_cold_owner *parent;struct wr_iot_driver_identity identity;
 char id[33];unsigned long long created;
 struct wr_iot_restart_profile_receipt profile;
 struct wr_iot_wan_followup_state wan;
};
/* Once claimed, retain this same context on every failure. */
int wr_iot_cold_release_begin(struct wr_iot_cold_release *,struct wr_iot_cold_handoff *);
/* May finish previously refused identity/WAN capture, each once. Does not
 * invoke a service or release any resource. */
int wr_iot_cold_release_current(struct wr_iot_cold_release *);
#endif
