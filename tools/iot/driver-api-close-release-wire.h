/* Linux-only operation14 for experimental no-host CLOSE owner release.
 * Uses the existing64-byte identity layout; no credentials or firmware fields. */
#ifndef WR_IOT_DRIVER_API_CLOSE_RELEASE_WIRE_H
#define WR_IOT_DRIVER_API_CLOSE_RELEASE_WIRE_H
#include "driver-api-close-wire.h"
#define WR_IOT_DRIVER_CLOSE_RELEASE_OPCODE 14U
static inline int wr_iot_driver_close_release_decode(
 struct wr_iot_driver_close_request *out,const unsigned char *wire,unsigned int length)
{
 unsigned char copy[WR_IOT_DRIVER_CLOSE_REQUEST_BYTES];unsigned int i;
 if(!out)return 0;
 if(!wire||length!=sizeof(copy)||wire[4]!=WR_IOT_DRIVER_CLOSE_RELEASE_OPCODE)
  return wr_iot_driver_close_request_decode(out,NULL,0);
 for(i=0;i<sizeof(copy);i++)copy[i]=wire[i];
 copy[4]=WR_IOT_DRIVER_CLOSE_REQUEST_OPCODE;
 return wr_iot_driver_close_request_decode(out,copy,sizeof(copy));
}
static inline int wr_iot_driver_close_release_encode(unsigned char *wire,
 unsigned int length,const struct wr_iot_driver_close_request *request)
{
 if(!wr_iot_driver_close_request_encode(wire,length,request))return 0;
 wire[4]=WR_IOT_DRIVER_CLOSE_RELEASE_OPCODE;return 1;
}
#endif
