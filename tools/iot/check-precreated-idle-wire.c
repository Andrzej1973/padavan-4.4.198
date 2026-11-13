#include <assert.h>
#include <string.h>
#include <stdio.h>
#include "precreated-idle-wire.h"
#include "driver-api-open-recovery-wire.h"
int main(void){
 unsigned char nonce[16]={1},wire[64],query[64],decoded[16];struct wr_iot_idle_result out;
 assert(wr_iot_idle_query_encode(query,64,nonce));
 assert(wr_iot_idle_query_decode(decoded,query,64)&&!memcmp(decoded,nonce,16));
 assert(wr_iot_idle_reply_encode(wire,64,nonce,1,2,3));
 assert(wr_iot_idle_reply_decode(&out,nonce,wire,64)&&out.serial==3);
 for(unsigned i=0;i<64;i++)if(i<24||i>=48){
  unsigned char bad[64];memcpy(bad,wire,64);bad[i]^=128;out.serial=99;
  assert(!wr_iot_idle_reply_decode(&out,nonce,bad,64)&&!out.serial);
 }
 for(unsigned n=0;n<64;n++)assert(!wr_iot_idle_reply_decode(&out,nonce,wire,n));
 struct wr_iot_driver_closed_result closed;struct wr_iot_driver_open_recovery_result recovery;
 assert(!wr_iot_driver_closed_decode(&closed,nonce,wire,64));
 assert(!wr_iot_driver_open_recovery_decode(&recovery,nonce,1,2,wire,64));
 assert(!wr_iot_idle_reply_decode(&out,nonce,query,64));
 assert(!wr_iot_idle_query_decode(decoded,wire,64));
 assert(!wr_iot_idle_reply_encode(wire,64,nonce,0,2,3));
 for(unsigned i=0;i<64;i++)assert(!wire[i]);
 puts("PASS initial-idle wire17/18: nonce, nonzero identity/serial, reserved/truncated rejection, output clearing and CLOSED/recovery type separation; endpoint uninstalled");
 return 0;
}
