/* New Linux-only operation 13: advance reference retirement of existing CLOSE.
 * Same fixed identity layout as operation10; deliberately incompatible opcode.
 * Routed in the isolated candidate common dispatcher. No RF/reopen status is returned. */
#ifndef WR_IOT_DRIVER_API_CLOSE_PROGRESS_WIRE_H
#define WR_IOT_DRIVER_API_CLOSE_PROGRESS_WIRE_H
#include "driver-api-close-wire.h"
#define WR_IOT_DRIVER_CLOSE_PROGRESS_OPCODE 13U
static inline int wr_iot_driver_close_progress_decode(
 struct wr_iot_driver_close_request *out,const unsigned char *wire,unsigned int length)
{
 unsigned char copy[WR_IOT_DRIVER_CLOSE_REQUEST_BYTES];unsigned int i;
 if(!out)return 0;
 if(!wire||length!=sizeof(copy)||wire[4]!=WR_IOT_DRIVER_CLOSE_PROGRESS_OPCODE)
  return wr_iot_driver_close_request_decode(out,NULL,0);
 for(i=0;i<sizeof(copy);i++)copy[i]=wire[i];
 copy[4]=WR_IOT_DRIVER_CLOSE_REQUEST_OPCODE;
 return wr_iot_driver_close_request_decode(out,copy,sizeof(copy));
}
static inline int wr_iot_driver_close_progress_encode(unsigned char *wire,
 unsigned int length,const struct wr_iot_driver_close_request *request)
{
 if(!wr_iot_driver_close_request_encode(wire,length,request))return 0;
 wire[4]=WR_IOT_DRIVER_CLOSE_PROGRESS_OPCODE;return 1;
}
#endif
