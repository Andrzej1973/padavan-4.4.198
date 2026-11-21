#ifndef WR_IOT_RADIO_OFF_OWNER_H
#define WR_IOT_RADIO_OFF_OWNER_H
#include <sys/types.h>
#include "config-snapshot-prepared.h"
#if WR_IOT_SAVED_CONFIG_SNAPSHOT_PREPARED == 1
#include "profile-history.h"
#endif
#include "control-record.h"
#include "radio-off-policy.h"
#include "physical-stop-wire.h"
/* Private RC state. Zero initialize; never copy a live owner. Terminal result
 * must be acknowledged before admitting another OFF. No radio/UI binding. */
struct wr_iot_radio_off_owner {pid_t owner;char id[33];unsigned long long created;int result,busy,policy_ready;struct wr_iot_radio_off_policy policy;struct wr_iot_physical_stop_request released;
#if WR_IOT_SAVED_CONFIG_SNAPSHOT_PREPARED == 1
 struct wr_iot_profile_binding profile_binding;
 struct wr_iot_restart_profile_receipt profile_receipt;
#endif
};
int wr_iot_radio_off_begin(struct wr_iot_radio_off_owner *,const struct wr_iot_control_request *);
/* Capture once under retained physical admission/guard, before terminal take. */
int wr_iot_radio_off_prepare(struct wr_iot_radio_off_owner *,int);
int wr_iot_radio_off_poll(struct wr_iot_radio_off_owner *);
/* One nonblocking physical step; policy refusal holds AUX/Main progress.
 * Pending normal shutdown may advance physical cleanup without SDK followup. */
int wr_iot_radio_off_step(struct wr_iot_radio_off_owner *,int);
int wr_iot_radio_off_take(struct wr_iot_radio_off_owner *);
#endif
