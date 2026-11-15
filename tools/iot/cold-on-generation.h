#ifndef WR_IOT_COLD_ON_GENERATION_H
#define WR_IOT_COLD_ON_GENERATION_H
#include "cold-on-admission.h"
#include "restart-profile.h"
enum wr_iot_cold_generation_phase {WR_COLD_GEN_IDLE,WR_COLD_GEN_CAPTURED,WR_COLD_GEN_GENERATED,WR_COLD_GEN_VERIFIED,WR_COLD_GEN_RESTORING,WR_COLD_GEN_RESTORED,WR_COLD_GEN_COMMITTED};
/* Stable-address owner borrows admission exclusively: admission.busy stays set
 * until a future checked handoff/retirement. No Main UP in this component. */
struct wr_iot_cold_generation {
 pid_t owner;int busy,reload,attempted,main_may_have_started;
 enum wr_iot_cold_generation_phase phase;
 struct wr_iot_cold_admission *admission;
 struct wr_iot_request desired;
};
int wr_iot_cold_generation_begin(struct wr_iot_cold_generation *,struct wr_iot_cold_admission *,const struct wr_iot_request *,int reload);
/* One phase per call. 1 verified profile, -1 restored baseline, 0 retained.
 * No guard release or repeated generation; restored state remains owned. */
int wr_iot_cold_generation_step(struct wr_iot_cold_generation *);
/* Fresh pre-UP DOWN origin check; refuses after possible Main UP. */
int wr_iot_cold_generation_origin_current(struct wr_iot_cold_generation *);
int wr_iot_cold_generation_abort(struct wr_iot_cold_generation *);
/* Pre-UP recovery only, pending shutdown retains ownership. Restores owned baseline
 * with fresh DOWN proof; retains profile/guards, never generates or opens. */
int wr_iot_cold_generation_recover(struct wr_iot_cold_generation *);
/* Checks selected profile: ON credentials or explicit saved OFF; no writes. */
int wr_iot_cold_generation_profile_current(const struct wr_iot_cold_generation *);
#endif
