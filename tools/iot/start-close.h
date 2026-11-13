/* Startup failure after a possible OPEN: retain the startup baseline while
 * obtaining CLOSE owner release. This does not tear down network resources,
 * release the snapshot, or authorize reopen. Caller serializes all contexts. */
#ifndef WR_IOT_START_CLOSE_H
#define WR_IOT_START_CLOSE_H
#include "start-admission.h"
#include "driver-open-controller.h"
#include "driver-close-controller.h"
struct wr_iot_start_close {
 pid_t owner;
 struct wr_iot_driver_attempt attempt;
 struct wr_iot_close_controller close;
 unsigned long long close_serial;
};
/* One bounded CLOSE recovery step. Returns1 only with fresh matching CLOSED
 * configuration after owner release. Original startup snapshot stays held. */
int wr_iot_start_close_step(struct wr_iot_start_close *,
 const struct wr_iot_start_admission *,const struct wr_iot_open_controller *);
#endif
