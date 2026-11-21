#ifndef WR_IOT_RADIO_ON_SHUTDOWN_H
#define WR_IOT_RADIO_ON_SHUTDOWN_H
#include "radio-on-shutdown-check.h"
enum wr_iot_on_shutdown_phase {WR_ON_STOP_IDLE,WR_ON_STOP_ADMITTED,WR_ON_STOP_DRAIN,WR_ON_STOP_CLOSED,WR_ON_STOP_REJECTED};
/* Stable children and borrowed restore; no copying or guard release. */
struct wr_iot_on_shutdown {
 pid_t owner;int busy;enum wr_iot_on_shutdown_phase phase;
 struct wr_iot_on_restore *restore;
 struct wr_iot_control_request input;struct wr_iot_rc_quiesce off;
};
/* Requires pending normal shutdown and exact already-handed-off restore.
 * Stores OFF identity only; no caller credentials retained. */
int wr_iot_on_shutdown_begin(struct wr_iot_on_shutdown *,struct wr_iot_on_restore *,const struct wr_iot_control_request *);
/* One existing backend/Guest OFF phase.1 fresh CLOSED or separately REJECTED,
 * retains baseline/root/guards; not a hardware retirement certificate. */
int wr_iot_on_shutdown_step(struct wr_iot_on_shutdown *);
#endif
