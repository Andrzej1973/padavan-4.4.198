#ifndef WR_IOT_RADIO_OFF_PROFILE_H
#define WR_IOT_RADIO_OFF_PROFILE_H
#include "radio-off-owner.h"
#include "radio-profile-state.h"
enum wr_iot_off_profile_phase {WR_OFF_PROFILE_IDLE,WR_OFF_PROFILE_CAPTURED,WR_OFF_PROFILE_GENERATED,WR_OFF_PROFILE_VERIFIED,WR_OFF_PROFILE_RESTORING,WR_OFF_PROFILE_RESTORED,WR_OFF_PROFILE_RETAINED};
/* Stable private context; baseline contains credentials, never publish/copy. */
struct wr_iot_off_profile {const struct wr_iot_off_profile *self;pid_t owner;int busy,reload,attempted;enum wr_iot_off_profile_phase phase;struct wr_iot_physical_stop_request released;struct wr_iot_radio_profile_state baseline;};
int wr_iot_off_profile_begin(struct wr_iot_off_profile *,const struct wr_iot_radio_off_owner *);
/* One phase:1 verified generated/current profile,-1 restored baseline,0 retained.
 * Neither return retires the context nor completes the SDK OFF lifecycle. */
int wr_iot_off_profile_step(struct wr_iot_off_profile *);
int wr_iot_rc_off_profile_current(void);
#endif
