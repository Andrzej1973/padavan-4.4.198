#ifndef WR_IOT_PHYSICAL_REBIND_CONTROLLER_H
#define WR_IOT_PHYSICAL_REBIND_CONTROLLER_H
#include <sys/types.h>
#include "physical-rebind-client.h"
#include "driver-api-client.h"
enum wr_iot_rebind_open_phase {WR_REBIND_OPEN_IDLE,WR_REBIND_OPEN_NOT_SUBMITTED,
 WR_REBIND_OPEN_RETAINED,WR_REBIND_OPEN_CURRENT};
struct wr_iot_rebind_open_controller {
 pid_t owner;int busy;
 enum wr_iot_rebind_open_phase phase;
 struct wr_iot_driver_attempt attempt;
};
/* Requires actual shutdown/service ownership. One submission maximum per
 * retained context, no credentials retained here. CURRENT is software driver
 * receipt only; network/isolation/runtime acceptance remains external. */
int wr_iot_rebind_open_submit(struct wr_iot_rebind_open_controller *,
 const struct wr_iot_physical_rebind_request *);
int wr_iot_rebind_open_current(struct wr_iot_rebind_open_controller *,
 struct wr_iot_driver_open_current_result *);
/* Recovery token does not set CURRENT or authorize retry/guard release. */
int wr_iot_rebind_open_recovery(const struct wr_iot_rebind_open_controller *,
 struct wr_iot_driver_open_recovery_result *);
#endif
