/* Caller serializes IoT operations and quiesces the BSS before bridge changes. */
#ifndef WR_IOT_BRIDGE_H
#define WR_IOT_BRIDGE_H
#include <stddef.h>
#include "types.h"
int wr_iot_bridge_prepare(const char *,const char *,const char *,const char *,const struct wr_iot_range *,size_t);
int wr_iot_bridge_remove(void);
int wr_iot_bridge_is_owned(void);
int wr_iot_bridge_attach(void);
int wr_iot_bridge_detach(void);
/* Caller installs isolation before UP and stops ra2 before either transition. */
int wr_iot_bridge_set_up(int enabled);
#endif
