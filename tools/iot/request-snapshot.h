/* Controller-owned NVRAM rollback state. Zero-initialize before take.
 * take holds the service guard until suspend/finish; nested staging is allowed.
 * Restore only after the controller has stopped/detached/removed its bridge.
 * Failed restore retains the snapshot and lock for an explicit retry. */
#ifndef WR_IOT_REQUEST_SNAPSHOT_H
#define WR_IOT_REQUEST_SNAPSHOT_H
#include <sys/types.h>
struct wr_iot_request_snapshot {
 int active,token,recovering,restored;
 pid_t owner;
 char values[9][80];
};
int wr_iot_request_snapshot_take(struct wr_iot_request_snapshot *);
int wr_iot_request_snapshot_restore(struct wr_iot_request_snapshot *);
int wr_iot_request_snapshot_finish(struct wr_iot_request_snapshot *);
/* Retain baseline across ACTIVE without retaining a nested service lock.
 * Resume before stop/recovery; failed acquisition leaves baseline intact. */
int wr_iot_request_snapshot_suspend(struct wr_iot_request_snapshot *);
int wr_iot_request_snapshot_resume(struct wr_iot_request_snapshot *);
#endif
