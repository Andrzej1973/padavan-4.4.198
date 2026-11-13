/* HTTPD-side observer. The owner exists only in PID1 RC, never in HTTPD.
 * Fixed private directory and peer identity; no path/PID/UID from HTTP input. */
#include "control-channel.h"
#include "status-endpoint.h"
int wr_iot_activation_result_observed(const struct wr_iot_control_result *result)
{
 return wr_iot_status_endpoint_query(WR_IOT_CONTROL_DIRECTORY,1,0,result);
}
