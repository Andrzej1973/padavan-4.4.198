#ifndef WR_IOT_RADIO_ON_GUEST_H
#define WR_IOT_RADIO_ON_GUEST_H
#include "radio-on-main.h"
#include "restart-guest-up.h"
enum wr_iot_on_guest_phase {WR_ON_GUEST_IDLE,WR_ON_GUEST_BRIDGE,WR_ON_GUEST_ISOLATE,WR_ON_GUEST_OPEN,WR_ON_GUEST_WAIT,WR_ON_GUEST_NO_SUBMISSION,
 WR_ON_GUEST_ADMIN_UP,WR_ON_GUEST_POLICY_OFF,WR_ON_GUEST_RECOVER_DOWN,WR_ON_GUEST_DOWN_OBSERVED};
struct wr_iot_on_guest {
 pid_t owner;int busy,desired,isolate,bridge_attempted,down_attempted;
 enum wr_iot_on_guest_phase phase;
 struct wr_iot_on_main *main;
};
/* Ordered DOWN bridge -> vendor router-mode L2 isolation -> UP.
 * Preserves Guest SDK policy; dedicated IoT routed isolation is separate.
 * Not scheduler-bound. Results are administrative/policy only, not Guest ready.
 * Retain original Main and generation objects; never copy live contexts. */
int wr_iot_on_guest_begin(struct wr_iot_on_guest *,struct wr_iot_on_main *);
int wr_iot_on_guest_step(struct wr_iot_on_guest *);
#endif
