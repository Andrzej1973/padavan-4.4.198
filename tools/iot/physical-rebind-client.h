#ifndef WR_IOT_PHYSICAL_REBIND_CLIENT_H
#define WR_IOT_PHYSICAL_REBIND_CLIENT_H
#include "physical-rebind-wire.h"
enum wr_iot_rebind_call_result {
 WR_REBIND_NOT_SUBMITTED,WR_REBIND_UNCERTAIN,WR_REBIND_IOCTL_RETURNED
};
/* Fixed ra2/existing CLOSED_CONFIG, one attempt. RETURNED is ioctl status only;
 * retain exact request/issuer for current driver receipt and recovery checks.
 * UNCERTAIN never authorizes retry OPEN, cleanup, or release of RC guards. */
enum wr_iot_rebind_call_result wr_iot_physical_rebind_call(
 const struct wr_iot_physical_rebind_request *);
#endif
