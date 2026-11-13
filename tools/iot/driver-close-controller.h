#ifndef WR_IOT_DRIVER_CLOSE_CONTROLLER_H
#define WR_IOT_DRIVER_CLOSE_CONTROLLER_H
#include "driver-api-client.h"
/* Caller serializes this context with the RC service owner. Phases distinguish reference retirement
 * from explicit experimental CLOSE-owner release. Network isolation remains independently
 * owned until the full quiescence and policy checks complete. */
enum wr_iot_close_phase {
 WR_IOT_CLOSE_IDLE,
 WR_IOT_CLOSE_SUBMITTED,
 WR_IOT_CLOSE_REFERENCE_RETIRED,
 WR_IOT_CLOSE_UNCERTAIN,
 WR_IOT_CLOSE_RELEASE_PENDING,
 WR_IOT_CLOSE_RELEASE_UNCERTAIN,
 WR_IOT_CLOSE_OWNER_RELEASED
};
struct wr_iot_close_controller {
 struct wr_iot_driver_close_request request;
 enum wr_iot_close_phase phase;
};
int wr_iot_close_controller_begin(struct wr_iot_close_controller *,
 const struct wr_iot_driver_attempt *,const struct wr_iot_driver_open_current_result *);
/* Explicit progress may reconcile an uncertain CLOSE with the same identity.
 * Kernel matching remains authoritative. This never submits CLOSE again. */
int wr_iot_close_controller_progress(struct wr_iot_close_controller *);
/* Advance only after reference retirement. Retains original identity across
 * uncertain release replies. Requires the experimental operation14 driver. */
int wr_iot_close_controller_release(struct wr_iot_close_controller *);
#endif
