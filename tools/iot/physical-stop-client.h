#ifndef WR_IOT_PHYSICAL_STOP_CLIENT_H
#define WR_IOT_PHYSICAL_STOP_CLIENT_H
#include "physical-stop-response.h"
enum wr_iot_physical_call_result {
 WR_PHYSICAL_CALL_NOT_SUBMITTED,
 WR_PHYSICAL_CALL_UNCERTAIN,
 WR_PHYSICAL_CALL_ACKNOWLEDGED
};
/* Fixed ra0, existing CLOSED_CONFIG ioctl, one call and no automatic retry.
 * Caller retains exact request and issuing task until terminal cleanup.
 * ACKNOWLEDGED means typed exact kernel response, not device/RF acceptance.
 * UNCERTAIN clears output; retain original request for QUERY/retry recovery. */
enum wr_iot_physical_call_result wr_iot_physical_stop_call(
 const struct wr_iot_physical_stop_request *,struct wr_iot_physical_stop_response *);
#endif
