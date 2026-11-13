/* Retained RC orchestration. Zero-initialize once; never copy a live object:
 * active-stop contains a pointer to this object's runner. This is not yet the
 * production mode/status adapter or scheduler. */
#ifndef WR_IOT_ACTIVATION_OWNER_H
#define WR_IOT_ACTIVATION_OWNER_H
#include "active-stop.h"
enum wr_iot_activation_owner_phase {
 WR_IOT_OWNER_IDLE,WR_IOT_OWNER_START,WR_IOT_OWNER_ACTIVE,
 WR_IOT_OWNER_STOP,WR_IOT_OWNER_OFF,WR_IOT_OWNER_REJECTED
};
struct wr_iot_activation_owner {
 pid_t owner;
 int busy;
 enum wr_iot_activation_owner_phase phase;
 struct wr_iot_start_runner start;
 struct wr_iot_active_stop stop;
};
/* Execute claims a new envelope once. START/STOP reject replay without mutation.
 * OFF requires this owner's ACTIVE ON, not inferred interface presence.
 * A fully recovered rejected START can be replaced; OFF->ON needs reopen proof
 * and is deliberately not routed through initial-never-opened admission. */
enum wr_iot_result_state wr_iot_activation_owner_execute(struct wr_iot_activation_owner *,
 const struct wr_iot_control_request *,int,int,int);
/* Exactly one bounded controller step using the original private context. */
enum wr_iot_result_state wr_iot_activation_owner_continue(struct wr_iot_activation_owner *,
 const char *,unsigned long long);
#endif
