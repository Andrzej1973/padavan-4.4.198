/* Normal OFF of a retained ACTIVE startup owner. No baseline restoration.
 * Caller retains both objects until terminal; zero-initialize stop once. */
#ifndef WR_IOT_ACTIVE_STOP_H
#define WR_IOT_ACTIVE_STOP_H
#include "start-runner.h"
struct wr_iot_active_stop {
 pid_t owner;
 char id[33];unsigned long long created;
 int busy,complete;
 struct wr_iot_start_runner *active;
 struct wr_iot_precreated_stop stop;
};
int wr_iot_active_stop_begin(struct wr_iot_active_stop *,struct wr_iot_start_runner *,
 const struct wr_iot_control_request *);
enum wr_iot_result_state wr_iot_active_stop_continue(struct wr_iot_active_stop *,
 const char *,unsigned long long);
#endif
