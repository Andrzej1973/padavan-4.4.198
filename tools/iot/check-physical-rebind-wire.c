#include <assert.h>
#include <string.h>
#include "physical-rebind-wire.h"
int main(void)
{
 struct wr_iot_physical_rebind_request r={0},out;
 unsigned char wire[216],bad[216];unsigned i,operation;
 r.physical=(struct wr_iot_physical_stop_request){.action=WR_STOP_RELEASE,.epoch=5,
  .generation=2,.open_token=3,.closed_serial=4,.attempt=6,.nonce={1}};
 r.open=(struct wr_iot_driver_open_request){.adapter_epoch=7,.device_generation=2,
  .request_id={9},.ssid_length=3,.password_length=8,.ssid="IoT",.password="password"};
 for(operation=1;operation<=2;operation++){
  unsigned length=operation==1?72:216;
  r.operation=operation;
  assert(wr_iot_physical_rebind_encode(wire,length,&r));
  assert(wr_iot_physical_rebind_decode(&out,wire,length)&&out.operation==operation);
  for(i=0;i<length;i++)assert(!wr_iot_physical_rebind_decode(&out,wire,i));
  for(i=0;i<8;i++){
   memcpy(bad,wire,length);bad[i]^=0x80;
   assert(!wr_iot_physical_rebind_decode(&out,bad,length));
   assert(!out.operation&&!out.open.password[0]);
  }
 }
 r.open.adapter_epoch=5;assert(!wr_iot_physical_rebind_encode(wire,216,&r));
 for(i=0;i<216;i++)assert(!wire[i]);
 r.open.adapter_epoch=7;
 r.open.device_generation++;assert(!wr_iot_physical_rebind_encode(wire,216,&r));
 r.open.device_generation--;r.physical.action=WR_STOP_CANCEL;
 assert(!wr_iot_physical_rebind_encode(wire,216,&r));
 wr_iot_physical_rebind_wipe(&r);assert(!r.operation&&!r.open.password[0]);return 0;
}
