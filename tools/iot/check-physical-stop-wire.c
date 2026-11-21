#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "physical-stop-wire.h"
int main(void){
 unsigned char wire[64],bad[64];struct wr_iot_physical_stop_request out;
 struct wr_iot_physical_stop_request r={.epoch=0x100000001ULL,.generation=2,.open_token=3,.closed_serial=0x200000004ULL,.nonce={1}};
 for(unsigned action=WR_STOP_ARM;action<=WR_STOP_RELEASE;action++){
  r.action=action;r.attempt=action==WR_STOP_ARM?0:0x300000001ULL;
  assert(wr_iot_physical_stop_request_encode(wire,64,&r));
  assert(wire[8]==0&&wire[11]==1&&wire[15]==1);
  assert(wr_iot_physical_stop_request_decode(&out,wire,64));
  assert(out.action==r.action&&out.epoch==r.epoch&&out.closed_serial==r.closed_serial&&out.attempt==r.attempt&&!memcmp(out.nonce,r.nonce,16));
  for(unsigned i=0;i<8;i++){
   memcpy(bad,wire,64);bad[i]^=0x80;memset(&out,0xff,sizeof(out));
   assert(!wr_iot_physical_stop_request_decode(&out,bad,64)&&!out.epoch&&!out.action&&!out.attempt);
  }
  for(unsigned field=8;field<=32;field+=8){memcpy(bad,wire,64);memset(bad+field,0,8);assert(!wr_iot_physical_stop_request_decode(&out,bad,64));}
  memcpy(bad,wire,64);memset(bad+48,0,16);assert(!wr_iot_physical_stop_request_decode(&out,bad,64));
  memcpy(bad,wire,64);memset(bad+40,0,8);if(action==WR_STOP_ARM)bad[47]=1;
  assert(!wr_iot_physical_stop_request_decode(&out,bad,64));
  for(unsigned n=0;n<64;n++)assert(!wr_iot_physical_stop_request_decode(&out,wire,n));
 }
 memset(wire,0xff,64);r.action=0;
 assert(!wr_iot_physical_stop_request_encode(wire,64,&r));
 for(unsigned i=0;i<64;i++)assert(!wire[i]);
 assert(!wr_iot_physical_stop_request_decode(&out,NULL,64));
 puts("PASS proposed physical-stop request wire:4 actions, full64-bit identities, reserved/header/zero/length rejection and cleared errors; no endpoint or completion acceptance");
}
