/* Controller-owned NVRAM rollback state. Zero-initialize before take.
 * take holds the service guard until suspend/finish; nested staging is allowed.
 * Restore only after the controller has stopped/detached/removed its bridge.
 * Failed restore retains the snapshot and lock for an explicit retry. */
#ifndef WR_IOT_REQUEST_SNAPSHOT_H
#define WR_IOT_REQUEST_SNAPSHOT_H
#include <sys/types.h>
struct wr_iot_request_snapshot {
 int active,token,recovering,restored,expected_valid,disabling,disable_stage,disable_mutated;
 unsigned int bridge_index;
 pid_t owner;
 char values[9][80];
 char expected[9][80];
};
int wr_iot_request_snapshot_take(struct wr_iot_request_snapshot *);
int wr_iot_request_snapshot_restore(struct wr_iot_request_snapshot *);
int wr_iot_request_snapshot_finish(struct wr_iot_request_snapshot *);
/* Retain baseline across ACTIVE without retaining a nested service lock.
 * Resume before stop/recovery; failed acquisition leaves baseline intact.
 * Suspend captures the current owned temporary values. Resume refuses foreign
 * changes before allowing baseline restoration; never overwrite them blindly.
 * This detects current value differences, not intervening change-and-revert. */
int wr_iot_request_snapshot_suspend(struct wr_iot_request_snapshot *);
int wr_iot_request_snapshot_resume(struct wr_iot_request_snapshot *);
/* Separate normal-OFF mode: capture CURRENT values with the owned bridge
 * present. Close gates only after administrative BSS DOWN; retain bridge for
 * DNS service recovery. Forget credentials only after bridge removal.
 * Restore/suspend are prohibited: normal OFF must never reopen old IoT gates.
 * Caller separately proves radio quiescence and full quarantine throughout. */
int wr_iot_request_disable_take(struct wr_iot_request_snapshot *);
/* Release only a read-only normal-OFF capture; never after attempted setters. */
int wr_iot_request_disable_cancel(struct wr_iot_request_snapshot *);
int wr_iot_request_disable_close_gates(struct wr_iot_request_snapshot *);
/* Read-only owned values check after gate closure, before profile mutation. */
int wr_iot_request_disable_ready(struct wr_iot_request_snapshot *);
int wr_iot_request_disable_forget(struct wr_iot_request_snapshot *);
#endif
