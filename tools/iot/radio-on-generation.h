#ifndef WR_IOT_RADIO_ON_GENERATION_H
#define WR_IOT_RADIO_ON_GENERATION_H
#include "radio-on-admission.h"
#include "restart-profile.h"
enum wr_iot_on_generation_phase {WR_ON_GEN_IDLE,WR_ON_GEN_CAPTURED,WR_ON_GEN_GENERATED,WR_ON_GEN_VERIFIED,WR_ON_GEN_RESTORING,WR_ON_GEN_RESTORED,WR_ON_GEN_COMMITTED};
/* Stable-address owner borrows admission exclusively: admission.busy stays set
 * until a future checked handoff/retirement. No Main UP in this component. */
struct wr_iot_on_generation {
 pid_t owner;int busy,reload,attempted,main_may_have_started;
 enum wr_iot_on_generation_phase phase;
 struct wr_iot_on_admission *admission;
 struct wr_iot_request desired;
};
int wr_iot_on_generation_begin(struct wr_iot_on_generation *,struct wr_iot_on_admission *,const struct wr_iot_request *,int reload);
/* One phase per call. 1 verified profile, -1 restored baseline, 0 retained.
 * No guard release or repeated generation; restored state remains owned. */
int wr_iot_on_generation_step(struct wr_iot_on_generation *);
/* Read-only retained origin check after possible Main UP; not readiness. */
int wr_iot_on_generation_origin_current(struct wr_iot_on_generation *);
int wr_iot_on_generation_abort(struct wr_iot_on_generation *);
/* Pre-UP recovery only, including pending shutdown. Restores owned baseline
 * with fresh DOWN proof; retains profile/guards, never generates or opens. */
int wr_iot_on_generation_recover(struct wr_iot_on_generation *);
#endif
