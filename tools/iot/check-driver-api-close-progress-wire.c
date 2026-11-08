#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "driver-api-close-progress-wire.h"
static void empty(const struct wr_iot_driver_close_request *r){
 assert(!r->adapter_epoch&&!r->device_generation&&!r->open_token);
 for(unsigned i=0;i<16;i++)assert(!r->open_request_id[i]);
}
int main(void){
 unsigned char wire[64],changed[64];
 struct wr_iot_driver_close_request r={{1},1,2,3},out;
 assert(wr_iot_driver_close_progress_encode(wire,64,&r)&&wire[4]==13);
 assert(wr_iot_driver_close_progress_decode(&out,wire,64));
 assert(!memcmp(out.open_request_id,r.open_request_id,16)&&out.open_token==3);
 assert(!wr_iot_driver_close_request_decode(&out,wire,64));empty(&out);
 assert(wr_iot_driver_close_request_encode(changed,64,&r));
 assert(!wr_iot_driver_close_progress_decode(&out,changed,64));empty(&out);
 for(unsigned i=0;i<64;i++)if(i<8||i>=48){
  memcpy(changed,wire,64);changed[i]^=0x80;memset(&out,0xff,sizeof(out));
  assert(!wr_iot_driver_close_progress_decode(&out,changed,64));empty(&out);
 }
 for(unsigned n=0;n<64;n++){
  memset(&out,0xff,sizeof(out));assert(!wr_iot_driver_close_progress_decode(&out,wire,n));empty(&out);
 }
 assert(!wr_iot_driver_close_progress_decode(&out,NULL,64));empty(&out);
 assert(!wr_iot_driver_close_progress_decode(NULL,wire,64));
 puts("PASS progress opcode13 strict wire; CLOSE opcode10 mutually rejected, reserved bytes/truncation clear output");
}
