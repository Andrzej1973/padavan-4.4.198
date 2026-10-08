/* Caller serializes IoT operations and quiesces the BSS before bridge changes. */
#ifndef WR_IOT_BRIDGE_H
#define WR_IOT_BRIDGE_H
#include <stddef.h>
#include "types.h"
int wr_iot_bridge_prepare(const char *,const char *,const char *,const char *,const struct wr_iot_range *,size_t);
int wr_iot_bridge_remove(void);
#endif
