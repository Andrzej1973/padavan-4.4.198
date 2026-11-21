#include "config-view-client.h"
#include "config-view-endpoint.h"
#include "config-view-runtime.h"
#ifndef WR_IOT_HTTP_RC_PID
#define WR_IOT_HTTP_RC_PID 1
#endif
#ifndef WR_IOT_HTTP_RC_UID
#define WR_IOT_HTTP_RC_UID 0
#endif
int wr_iot_http_view_read(struct wr_iot_config_view *out,char revision[33])
{
 return wr_iot_config_view_endpoint_query(WR_IOT_CONFIG_VIEW_DIRECTORY,WR_IOT_HTTP_RC_PID,
                                         WR_IOT_HTTP_RC_UID,out,revision);
}
