#ifndef WR_IOT_CONFIG_EDIT_SERVER_H
#define WR_IOT_CONFIG_EDIT_SERVER_H
#include "control-channel.h"
#include "config-view.h"
int wr_iot_rc_edit_backend_install(void);
int wr_iot_rc_edit_backend_ready(void);
int wr_iot_rc_edit_view(unsigned int,struct wr_iot_config_view *,char[33]);
int wr_iot_rc_edit_observed(const struct wr_iot_control_result *);
#endif
