#ifndef WR_IOT_CONFIG_VIEW_RUNTIME_H
#define WR_IOT_CONFIG_VIEW_RUNTIME_H
#include "control-channel.h"
#ifndef WR_IOT_CONFIG_VIEW_DIRECTORY
#define WR_IOT_CONFIG_VIEW_DIRECTORY WR_IOT_CONTROL_DIRECTORY "/view"
#endif
int wr_iot_rc_view_runtime_install(void);
int wr_iot_rc_view_runtime_close(void);
#endif
