/* Linux-only CLOSE: legacy operation10 and explicit deferral operation21.
 * Carries original successful OPEN identity only, never SSID/password.
 * Syntax acceptance cannot authorize mutation, retry or isolation release. */
#ifndef WR_IOT_DRIVER_API_CLOSE_WIRE_H
#define WR_IOT_DRIVER_API_CLOSE_WIRE_H
#include "driver-api-wire.h"
#define WR_IOT_DRIVER_CLOSE_REQUEST_BYTES 64U
#define WR_IOT_DRIVER_CLOSE_REQUEST_OPCODE 10U
/* Explicit Linux-only contract: EBUSY before admission may be attempted later.
 * Legacy operation10 is preserved and its decoder must reject this opcode.
 * WRI2 operations19/20 are Main-DOWN observation;21 is separately reserved. */
#define WR_IOT_DRIVER_CLOSE_DEFER_REQUEST_OPCODE 21U
struct wr_iot_driver_close_request {
 unsigned char open_request_id[16];
 unsigned long long adapter_epoch,device_generation,open_token;
};
static inline int wr_iot_driver_close_request_decode(
 struct wr_iot_driver_close_request *out,const unsigned char *wire,unsigned int length)
{
 unsigned int i,nonzero=0;
 if(!out)return 0;
 for(i=0;i<16;i++)out->open_request_id[i]=0;
 out->adapter_epoch=out->device_generation=out->open_token=0;
 if(!wire||length!=WR_IOT_DRIVER_CLOSE_REQUEST_BYTES||wire[0]!='W'||wire[1]!='R'||
    wire[2]!='I'||wire[3]!='2'||wire[4]!=WR_IOT_DRIVER_CLOSE_REQUEST_OPCODE)return 0;
 for(i=5;i<8;i++)if(wire[i])return 0;
 for(i=48;i<64;i++)if(wire[i])return 0;
 for(i=0;i<16;i++)nonzero|=wire[8+i];
 if(!nonzero||!wr_iot_driver_get64(wire+24)||!wr_iot_driver_get64(wire+32)||!wr_iot_driver_get64(wire+40))return 0;
 for(i=0;i<16;i++)out->open_request_id[i]=wire[8+i];
 out->adapter_epoch=wr_iot_driver_get64(wire+24);
 out->device_generation=wr_iot_driver_get64(wire+32);
 out->open_token=wr_iot_driver_get64(wire+40);return 1;
}
static inline int wr_iot_driver_close_request_encode(unsigned char *wire,unsigned int length,
 const struct wr_iot_driver_close_request *request)
{
 unsigned int i,nonzero=0;
 if(!wire||length!=WR_IOT_DRIVER_CLOSE_REQUEST_BYTES)return 0;
 for(i=0;i<length;i++)wire[i]=0;
 if(!request||!request->adapter_epoch||!request->device_generation||!request->open_token)return 0;
 for(i=0;i<16;i++)nonzero|=request->open_request_id[i];
 if(!nonzero)return 0;
 wire[0]='W';wire[1]='R';wire[2]='I';wire[3]='2';wire[4]=WR_IOT_DRIVER_CLOSE_REQUEST_OPCODE;
 for(i=0;i<16;i++)wire[8+i]=request->open_request_id[i];
 wr_iot_driver_put64(wire+24,request->adapter_epoch);
 wr_iot_driver_put64(wire+32,request->device_generation);
 wr_iot_driver_put64(wire+40,request->open_token);return 1;
}
static inline int wr_iot_driver_close_defer_encode(unsigned char *wire,unsigned int length,
 const struct wr_iot_driver_close_request *request)
{
 if(!wr_iot_driver_close_request_encode(wire,length,request))return 0;
 wire[4]=WR_IOT_DRIVER_CLOSE_DEFER_REQUEST_OPCODE;return 1;
}
static inline int wr_iot_driver_close_defer_decode(struct wr_iot_driver_close_request *out,
 const unsigned char *wire,unsigned int length)
{
 unsigned char copy[WR_IOT_DRIVER_CLOSE_REQUEST_BYTES];unsigned int i;
 if(!out)return 0;
 /* Use the old decoder's clearing contract even for null/short new input. */
 if(!wire||length!=sizeof(copy)||wire[4]!=WR_IOT_DRIVER_CLOSE_DEFER_REQUEST_OPCODE)
  return wr_iot_driver_close_request_decode(out,0,0);
 for(i=0;i<sizeof(copy);i++)copy[i]=wire[i];
 copy[4]=WR_IOT_DRIVER_CLOSE_REQUEST_OPCODE;
 return wr_iot_driver_close_request_decode(out,copy,sizeof(copy));
}
#endif
