/* Serialized RC owner calls outside signal context with its service guard,
 * staged request, isolated bridge/services and policy already prepared.
 * Outer shutdown admission must exclude fatal-signal teardown throughout;
 * the service guard alone does not fence the stock signal handler.
 * This object prevents resubmitting OPEN after any attempted transaction;
 * it owns only nonsecret attempt metadata, not network rollback or RF proof. */
#ifndef WR_IOT_DRIVER_OPEN_CONTROLLER_H
#define WR_IOT_DRIVER_OPEN_CONTROLLER_H
#include "driver-api-client.h"
#include <sys/types.h>
enum wr_iot_open_phase {
 WR_IOT_OPEN_IDLE,WR_IOT_OPEN_SUBMITTING,WR_IOT_OPEN_NOT_SUBMITTED,
 WR_IOT_OPEN_CONFIRMED,WR_IOT_OPEN_RECOVERY
};
struct wr_iot_open_controller {
 struct wr_iot_driver_attempt attempt;
 pid_t owner;
 enum wr_iot_open_phase phase;
};
/* Zero-initialize. 1 requires strict driver ON plus current network observation.
 * Failure after submission retains identity for CLOSE, never another OPEN. */
int wr_iot_open_controller_submit(struct wr_iot_open_controller *,const char *,
 const struct wr_iot_request *);
/* Read-only recovery token; no phase change, retry or acceptance permission. */
int wr_iot_open_controller_recovery_read(const struct wr_iot_open_controller *,
 struct wr_iot_driver_open_recovery_result *);
#endif
