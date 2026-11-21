#include <assert.h>
#include <string.h>
#include <stdio.h>
#include "driver-api-open-recovery-wire.h"
#include "driver-api-open-current-wire.h"
int main(void){
 unsigned char nonce[16]={1},wire[64],query[64],decoded[16];
 struct wr_iot_driver_open_recovery_result out;
 assert(wr_iot_driver_open_recovery_query_encode(query,64,nonce));
 assert(wr_iot_driver_open_recovery_query_decode(decoded,query,64)&&!memcmp(decoded,nonce,16));
 assert(wr_iot_driver_open_recovery_encode(wire,64,nonce,1,2,3));
 assert(wr_iot_driver_open_recovery_decode(&out,nonce,1,2,wire,64)&&out.open_token==3);
 struct wr_iot_driver_open_current_result normal;
 assert(!wr_iot_driver_open_current_decode(&normal,nonce,1,2,wire,64));
 unsigned char normal_wire[64];
 assert(wr_iot_driver_open_current_encode(normal_wire,64,nonce,1,2,3));
 assert(!wr_iot_driver_open_recovery_decode(&out,nonce,1,2,normal_wire,64));
 for(unsigned i=0;i<64;i++)if(i<8||i>=48){
  unsigned char copy[64];memcpy(copy,wire,64);copy[i]^=128;out.open_token=99;
  assert(!wr_iot_driver_open_recovery_decode(&out,nonce,1,2,copy,64)&&!out.open_token);
 }
 nonce[0]=2;assert(!wr_iot_driver_open_recovery_decode(&out,nonce,1,2,wire,64)&&!out.open_token);nonce[0]=1;
 assert(!wr_iot_driver_open_recovery_decode(&out,nonce,2,2,wire,64)&&!out.open_token);
 assert(!wr_iot_driver_open_recovery_decode(&out,nonce,1,3,wire,64)&&!out.open_token);
 assert(!wr_iot_driver_open_recovery_decode(&out,nonce,1,2,query,64));
 struct wr_iot_driver_close_request close;
 assert(!wr_iot_driver_close_request_decode(&close,wire,64));
 struct wr_iot_driver_closed_result closed;
 assert(!wr_iot_driver_closed_decode(&closed,nonce,wire,64));
 assert(!wr_iot_driver_open_recovery_query_decode(decoded,wire,64));
 for(unsigned i=0;i<16;i++)assert(!decoded[i]);
 assert(!wr_iot_driver_open_recovery_encode(wire,64,nonce,1,2,0));
 for(unsigned i=0;i<64;i++)assert(!wire[i]);
 puts("PASS recovery-only OPEN receipt wire: nonce/epoch/generation-bound token, output clearing and request/CLOSED type separation; not a lifetime or RF lease");
}
