#include <assert.h>
#include <string.h>
#include <stdio.h>
#include "driver-api-close-wire.h"
static void cleared(const struct wr_iot_driver_close_request *r){
 unsigned i;for(i=0;i<16;i++)assert(!r->open_request_id[i]);
 assert(!r->adapter_epoch&&!r->device_generation&&!r->open_token);
}
int main(void){
 struct wr_iot_driver_close_request r={{1},0x0102030405060708ULL,2,3},out;
 unsigned char wire[64],copy[64];
 assert(wr_iot_driver_close_request_encode(wire,64,&r));
 assert(wire[24]==1&&wire[31]==8);
 assert(wr_iot_driver_close_request_decode(&out,wire,64));
 assert(!memcmp(r.open_request_id,out.open_request_id,16)&&r.adapter_epoch==out.adapter_epoch&&out.device_generation==2&&out.open_token==3);
 for(unsigned i=0;i<64;i++)if(i<8||i>=48){
  memcpy(copy,wire,64);copy[i]^=0x80;memset(&out,0xff,sizeof(out));
  assert(!wr_iot_driver_close_request_decode(&out,copy,64));cleared(&out);
 }
 for(unsigned n=0;n<4;n++){
  memcpy(copy,wire,64);
  unsigned start=n?24+8*(n-1):8,len=n?8:16;
  memset(copy+start,0,len);memset(&out,0xff,sizeof(out));
  assert(!wr_iot_driver_close_request_decode(&out,copy,64));cleared(&out);
 }
 for(unsigned length=0;length<70;length++)if(length!=64){
  memset(&out,0xff,sizeof(out));assert(!wr_iot_driver_close_request_decode(&out,wire,length));cleared(&out);
 }
 struct wr_iot_driver_closed_result closed;
 struct wr_iot_driver_refusal_result refused;
 struct wr_iot_driver_uncertain_result uncertain;
 assert(!wr_iot_driver_closed_decode(&closed,r.open_request_id,wire,64));
 assert(!wr_iot_driver_refusal_decode(&refused,r.open_request_id,wire,64));
 assert(!wr_iot_driver_uncertain_decode(&uncertain,r.open_request_id,wire,64));
 r.open_token=0;memset(wire,0xff,64);assert(!wr_iot_driver_close_request_encode(wire,64,&r));
 for(unsigned i=0;i<64;i++)assert(!wire[i]);
 puts("PASS proposed CLOSE syntax: big-endian identity, reserved/zero/length rejection, output cleared and never decoded as CLOSED/refusal/uncertainty receipt; endpoint unbound");
}
