#ifndef WR_IOT_COLD_ON_HANDOFF_H
#define WR_IOT_COLD_ON_HANDOFF_H
#include "cold-on-owner.h"
enum wr_iot_cold_handoff_phase {WR_COLD_HANDOFF_IDLE,WR_COLD_HANDOFF_RETAINED,WR_COLD_HANDOFF_WAIT,WR_COLD_HANDOFF_ACTIVE};
struct wr_iot_cold_handoff {
 pid_t owner;int busy,attempted,backend_claimed;enum wr_iot_cold_handoff_phase phase;
 struct wr_iot_cold_owner *parent;struct wr_iot_driver_identity identity;
 char id[33];unsigned long long created;
};
/* 1 claims the handoff attempt even if backend refuses; never replay begin.
 * Keep parent and handoff at stable addresses through checked retirement. */
int wr_iot_cold_handoff_begin(struct wr_iot_cold_handoff *,struct wr_iot_cold_owner *);
/* One bound backend continuation; true only with fresh full ACTIVE proof.
 * No profile/guard/root release and no post-UP shutdown performed here. */
int wr_iot_cold_handoff_step(struct wr_iot_cold_handoff *);
int wr_iot_cold_handoff_current(struct wr_iot_cold_handoff *);
#endif
