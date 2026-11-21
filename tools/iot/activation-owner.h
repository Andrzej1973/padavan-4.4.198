/* Retained RC orchestration. Zero-initialize once; never copy a live object:
 * active-stop contains a pointer to this object's runner. This is not yet the
 * production mode/status adapter or scheduler. */
#ifndef WR_IOT_ACTIVATION_OWNER_H
#define WR_IOT_ACTIVATION_OWNER_H
#include "active-stop.h"
#include "initial-off.h"
enum wr_iot_activation_owner_phase {
 WR_IOT_OWNER_IDLE,WR_IOT_OWNER_START,WR_IOT_OWNER_ACTIVE,
 WR_IOT_OWNER_STOP,WR_IOT_OWNER_OFF,WR_IOT_OWNER_REJECTED,WR_IOT_OWNER_INITIAL_OFF
};
struct wr_iot_activation_owner {
 pid_t owner;
 int busy;
 enum wr_iot_activation_owner_phase phase;
 struct wr_iot_initial_off initial_off;
 struct wr_iot_start_runner start;
 struct wr_iot_active_stop stop;
};
/* Execute claims a new envelope once. START/STOP reject replay without mutation.
 * OFF requires owned ACTIVE or a fresh initial-never-opened observation,
 * never inferred interface presence.
 * A fully recovered rejected START can be replaced. OFF->ON uses a fresh
 * retained CLOSED witness, never initial-never-opened admission. Rejected
 * reopen after a submitted OPEN requires its own completed rollback/CLOSE witness. */
enum wr_iot_result_state wr_iot_activation_owner_execute(struct wr_iot_activation_owner *,
 const struct wr_iot_control_request *,int,int,int);
/* Exactly one bounded controller step using the original private context. */
enum wr_iot_result_state wr_iot_activation_owner_continue(struct wr_iot_activation_owner *,
 const char *,unsigned long long);
#endif
