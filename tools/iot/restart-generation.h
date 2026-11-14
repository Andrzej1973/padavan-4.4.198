/* Profile owner before Main startup. Stable-address retained context; never
 * copy while active. Caller holds the physical restart/service guards. */
#ifndef WR_IOT_RESTART_GENERATION_H
#define WR_IOT_RESTART_GENERATION_H
#include "radio-profile-state.h"
#include "restart-profile-receipt.h"
#include "rc-physical-stop.h"
enum wr_iot_restart_generation_phase {WR_RESTART_GEN_IDLE,WR_RESTART_GEN_CAPTURED,
 WR_RESTART_GEN_UNCERTAIN,WR_RESTART_GEN_GENERATED,WR_RESTART_GEN_VERIFIED,
 WR_RESTART_GEN_RECOVERING,WR_RESTART_GEN_RESTORED,WR_RESTART_GEN_ROLLED_BACK,WR_RESTART_GEN_COMMITTED};
struct wr_iot_restart_generation {
 pid_t owner;int busy;
 int main_may_have_started; /* Monotonic: prohibits pre-start profile restore. */
 enum wr_iot_restart_generation_phase phase;
 struct wr_iot_rc_physical_resume origin;
 struct wr_iot_radio_profile_state profile;
 struct wr_iot_restart_profile_receipt rollback_receipt;
};
int wr_iot_restart_generation_begin(struct wr_iot_restart_generation *);
/* At most one generator/restore/finish phase.1 only fresh VERIFIED, baseline
 * still held. No Main UP or outer guard release; no implicit generator retry. */
int wr_iot_restart_generation_step(struct wr_iot_restart_generation *);
/* Read-only exact retained physical context; valid also after Main UP. */
int wr_iot_restart_generation_origin_current(const struct wr_iot_restart_generation *);
/* Before any possible Main UP: request checked baseline restoration. */
int wr_iot_restart_generation_abort(struct wr_iot_restart_generation *);
/* Post-rollback proof without copied credentials. No fence release by itself. */
int wr_iot_restart_generation_rollback_current(const struct wr_iot_restart_generation *);
#endif
