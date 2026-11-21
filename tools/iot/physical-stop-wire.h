/* Proposed Linux-only request syntax. No ioctl/opcode is installed by this
 * header. A decoded request is NOT a teardown or lifetime permission. */
#ifndef WR_IOT_PHYSICAL_STOP_WIRE_H
#define WR_IOT_PHYSICAL_STOP_WIRE_H
#include "driver-api-wire.h"
#define WR_IOT_PHYSICAL_STOP_WIRE_BYTES 64U
enum wr_iot_physical_stop_action {WR_STOP_ARM=1,WR_STOP_QUERY,WR_STOP_CANCEL,WR_STOP_RELEASE};
struct wr_iot_physical_stop_request {
 unsigned int action;
 unsigned long long epoch,generation,open_token,closed_serial,attempt;
 unsigned char nonce[16];
};
static inline int wr_iot_physical_stop_request_valid(const struct wr_iot_physical_stop_request *r)
{
 unsigned i,nonzero=0;
 if(!r||r->action<WR_STOP_ARM||r->action>WR_STOP_RELEASE||
    !r->epoch||!r->generation||!r->open_token||!r->closed_serial||
    (r->action==WR_STOP_ARM?r->attempt!=0:r->attempt==0))return 0;
 for(i=0;i<16;i++)nonzero|=r->nonce[i];
 return nonzero!=0;
}
static inline int wr_iot_physical_stop_request_encode(unsigned char *wire,
 unsigned int length,const struct wr_iot_physical_stop_request *input)
{
 struct wr_iot_physical_stop_request r;unsigned i;
 if(!wire||length!=WR_IOT_PHYSICAL_STOP_WIRE_BYTES)return 0;
 if(input)r=*input;
 for(i=0;i<length;i++)wire[i]=0;
 if(!input||!wr_iot_physical_stop_request_valid(&r))return 0;
 wire[0]='W';wire[1]='P';wire[2]='S';wire[3]='Q';wire[4]=1;wire[5]=(unsigned char)r.action;
 wr_iot_driver_put64(wire+8,r.epoch);wr_iot_driver_put64(wire+16,r.generation);
 wr_iot_driver_put64(wire+24,r.open_token);wr_iot_driver_put64(wire+32,r.closed_serial);
 wr_iot_driver_put64(wire+40,r.attempt);
 for(i=0;i<16;i++)wire[48+i]=r.nonce[i];
 return 1;
}
static inline int wr_iot_physical_stop_request_decode(struct wr_iot_physical_stop_request *out,
 const unsigned char *wire,unsigned int length)
{
 struct wr_iot_physical_stop_request r={0};unsigned i;
 if(!out)return 0;
 /* Parse to local storage so input/output overlap never destroys the wire. */
 if(wire&&length==WR_IOT_PHYSICAL_STOP_WIRE_BYTES&&
    wire[0]=='W'&&wire[1]=='P'&&wire[2]=='S'&&wire[3]=='Q'&&
    wire[4]==1&&!wire[6]&&!wire[7]){
  r.action=wire[5];r.epoch=wr_iot_driver_get64(wire+8);r.generation=wr_iot_driver_get64(wire+16);
  r.open_token=wr_iot_driver_get64(wire+24);r.closed_serial=wr_iot_driver_get64(wire+32);
  r.attempt=wr_iot_driver_get64(wire+40);
  for(i=0;i<16;i++)r.nonce[i]=wire[48+i];
  if(wr_iot_physical_stop_request_valid(&r)){*out=r;return 1;}
 }
 {struct wr_iot_physical_stop_request empty={0};*out=empty;}return 0;
}
#endif
