#ifndef WR_IOT_PHYSICAL_INITIAL_CLIENT_H
#define WR_IOT_PHYSICAL_INITIAL_CLIENT_H
#include "physical-initial-wire.h"
#include "physical-stop-client.h" /* Shared transport result enum only. */
/* Fixed ra0/0x89fd, one syscall attempt. Preserve exact issuer/request after
 * UNCERTAIN. ACKNOWLEDGED is protocol correlation, not RF/runtime acceptance. */
enum wr_iot_physical_call_result wr_iot_physical_initial_call(
 const struct wr_iot_physical_initial_request *,struct wr_iot_physical_initial_response *);
#endif
