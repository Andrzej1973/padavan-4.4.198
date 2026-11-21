#ifndef WR_IOT_RADIO_OFF_FOLLOWUP_H
#define WR_IOT_RADIO_OFF_FOLLOWUP_H
#include "radio-off-profile.h"
#include "restart-profile-receipt.h"
#include "radio-off-wan.h"
#include "restart-terminal-iapp.h"
enum wr_iot_off_followup_phase {WR_OFF_FOLLOWUP_IDLE,WR_OFF_FOLLOWUP_PROFILE_BEGIN,WR_OFF_FOLLOWUP_PROFILE,WR_OFF_FOLLOWUP_STATE,WR_OFF_FOLLOWUP_BRIDGE,WR_OFF_FOLLOWUP_BRIDGE_VERIFY,WR_OFF_FOLLOWUP_AUTH,WR_OFF_FOLLOWUP_NETWORK_PENDING,WR_OFF_FOLLOWUP_WAN,WR_OFF_FOLLOWUP_POSTWAN,WR_OFF_FOLLOWUP_IAPP_PENDING,WR_OFF_FOLLOWUP_IAPP,WR_OFF_FOLLOWUP_FINAL_PENDING,WR_OFF_FOLLOWUP_FINALIZING,WR_OFF_FOLLOWUP_DONE,WR_OFF_FOLLOWUP_RETAINED};
/* Stable-address private owner; profile baseline contains credentials.
 * NETWORK_PENDING is unfinished, never a completed OFF result. */
struct wr_iot_off_followup {pid_t owner;int busy,state_attempted,auth_attempted;unsigned bridge_slot,bridge_verify,postwan_slot;const struct wr_iot_radio_off_owner *off;enum wr_iot_off_followup_phase phase;struct wr_iot_radio_off_policy policy;struct wr_iot_physical_stop_request released;struct wr_iot_off_profile profile;struct wr_iot_off_wan wan;struct wr_iot_iapp_child child;struct wr_iot_terminal_iapp iapp;struct wr_iot_radio_stop_fence finish_fence;int finish_guard;struct wr_iot_radio_off_owner *finish_off;
#if WR_IOT_SAVED_CONFIG_SNAPSHOT_PREPARED == 1
 struct wr_iot_restart_profile_receipt profile_receipt;
#endif
};
int wr_iot_off_followup_begin(struct wr_iot_off_followup *,const struct wr_iot_radio_off_owner *);
/* Advances one phase, returns current phase; never acknowledges/clears OFF. */
/* Read-only final preflight under caller-owned guard. Does not retire baseline. */
/* Exact owner cleanup under a new fence; failure retains same fence/guard.
 * Does not flash, reopen or prove physical runtime acceptance. */
int wr_iot_off_followup_finish(struct wr_iot_off_followup *,struct wr_iot_radio_off_owner *);
int wr_iot_off_followup_final_current(const struct wr_iot_off_followup *);
enum wr_iot_off_followup_phase wr_iot_off_followup_step(struct wr_iot_off_followup *);
#endif
