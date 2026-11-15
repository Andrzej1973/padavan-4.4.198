#ifndef WR_IOT_COLD_ON_GUEST_H
#define WR_IOT_COLD_ON_GUEST_H
#include "cold-on-main.h"
#include "restart-guest-up.h"
enum wr_iot_cold_guest_phase {WR_COLD_GUEST_IDLE,WR_COLD_GUEST_BRIDGE,WR_COLD_GUEST_ISOLATE,WR_COLD_GUEST_OPEN,WR_COLD_GUEST_WAIT,WR_COLD_GUEST_NO_SUBMISSION,
 WR_COLD_GUEST_ADMIN_UP,WR_COLD_GUEST_POLICY_OFF,WR_COLD_GUEST_RECOVER_DOWN,WR_COLD_GUEST_DOWN_OBSERVED};
struct wr_iot_cold_guest {
 pid_t owner;int busy,desired,isolate,bridge_attempted,down_attempted;
 enum wr_iot_cold_guest_phase phase;
 struct wr_iot_cold_main *main;
};
/* Ordered DOWN bridge -> vendor router-mode L2 isolation -> UP.
 * Preserves Guest SDK policy; dedicated IoT routed isolation is separate.
 * Not scheduler-bound. Results are administrative/policy only, not Guest ready.
 * Retain original Main and generation objects; never copy live contexts. */
int wr_iot_cold_guest_begin(struct wr_iot_cold_guest *,struct wr_iot_cold_main *);
int wr_iot_cold_guest_step(struct wr_iot_cold_guest *);
#endif
