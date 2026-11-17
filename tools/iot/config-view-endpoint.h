#ifndef WR_IOT_CONFIG_VIEW_ENDPOINT_H
#define WR_IOT_CONFIG_VIEW_ENDPOINT_H
#include "status-endpoint.h"
#include "config-view-channel.h"
int wr_iot_config_view_endpoint_step(struct wr_iot_status_endpoint *,unsigned int,
 int (*)(unsigned int,struct wr_iot_config_view *,char[33]));
int wr_iot_config_view_endpoint_query(const char *,pid_t,uid_t,struct wr_iot_config_view *,char[33]);
#endif
