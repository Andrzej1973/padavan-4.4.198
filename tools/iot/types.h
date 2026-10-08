#ifndef WR_IOT_TYPES_H
#define WR_IOT_TYPES_H
#include <stdint.h>
struct wr_iot_range { uint32_t first,last; };
struct wr_iot_subnet { uint32_t gateway,mask,network,broadcast,start,end; };
#endif
