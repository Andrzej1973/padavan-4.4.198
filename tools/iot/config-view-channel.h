#ifndef WR_IOT_CONFIG_VIEW_CHANNEL_H
#define WR_IOT_CONFIG_VIEW_CHANNEL_H
#include <sys/types.h>
#include "config-view.h"
int wr_iot_config_view_query(int,pid_t,uid_t,struct wr_iot_config_view *,char[33]);
int wr_iot_config_view_serve_once(int,uid_t,unsigned int,
 int (*)(unsigned int,struct wr_iot_config_view *,char[33]));
#endif
