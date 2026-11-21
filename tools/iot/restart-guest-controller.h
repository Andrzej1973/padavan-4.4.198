#ifndef WR_IOT_RESTART_GUEST_CONTROLLER_H
#define WR_IOT_RESTART_GUEST_CONTROLLER_H
#include "restart-main-controller.h"
#include "restart-guest-up.h"
enum wr_iot_restart_guest_phase {WR_GUEST_IDLE,WR_GUEST_BRIDGE,WR_GUEST_ISOLATE,WR_GUEST_OPEN,WR_GUEST_WAIT,WR_GUEST_NO_SUBMISSION,
 WR_GUEST_ADMIN_UP,WR_GUEST_POLICY_OFF,WR_GUEST_RECOVER_DOWN,WR_GUEST_DOWN_OBSERVED};
struct wr_iot_restart_guest {
 pid_t owner;int busy,desired,isolate,bridge_attempted,down_attempted;
 enum wr_iot_restart_guest_phase phase;
 struct wr_iot_restart_main *main;
};
/* Ordered DOWN bridge -> vendor router-mode L2 isolation -> UP.
 * Preserves Guest SDK policy; dedicated IoT routed isolation is separate.
 * Not scheduler-bound. Results are administrative/policy only, not Guest ready.
 * Retain original Main and generation objects; never copy live contexts. */
int wr_iot_restart_guest_begin(struct wr_iot_restart_guest *,struct wr_iot_restart_main *);
int wr_iot_restart_guest_step(struct wr_iot_restart_guest *);
#endif
