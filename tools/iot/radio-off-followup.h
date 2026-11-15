#ifndef WR_IOT_RADIO_OFF_FOLLOWUP_H
#define WR_IOT_RADIO_OFF_FOLLOWUP_H
#include "radio-off-profile.h"
enum wr_iot_off_followup_phase {WR_OFF_FOLLOWUP_IDLE,WR_OFF_FOLLOWUP_PROFILE_BEGIN,WR_OFF_FOLLOWUP_PROFILE,WR_OFF_FOLLOWUP_STATE,WR_OFF_FOLLOWUP_BRIDGE,WR_OFF_FOLLOWUP_BRIDGE_VERIFY,WR_OFF_FOLLOWUP_NETWORK_PENDING,WR_OFF_FOLLOWUP_RETAINED};
/* Stable-address private owner; profile baseline contains credentials.
 * NETWORK_PENDING is unfinished, never a completed OFF result. */
struct wr_iot_off_followup {pid_t owner;int busy,state_attempted;unsigned bridge_slot,bridge_verify;const struct wr_iot_radio_off_owner *off;enum wr_iot_off_followup_phase phase;struct wr_iot_radio_off_policy policy;struct wr_iot_physical_stop_request released;struct wr_iot_off_profile profile;};
int wr_iot_off_followup_begin(struct wr_iot_off_followup *,const struct wr_iot_radio_off_owner *);
/* Advances one phase, returns current phase; never acknowledges/clears OFF. */
enum wr_iot_off_followup_phase wr_iot_off_followup_step(struct wr_iot_off_followup *);
#endif
