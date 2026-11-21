#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "physical-stop-response.h"
int main(void){
 unsigned char wire[64],bad[64];struct wr_iot_physical_stop_response out;
 struct wr_iot_physical_stop_request r={.epoch=1,.generation=2,.open_token=3,.closed_serial=0x100000004ULL,.nonce={1}};
 for(unsigned action=WR_STOP_ARM;action<=WR_STOP_RELEASE;action++){
  r.action=action;r.attempt=action==WR_STOP_ARM?0:0x200000003ULL;
  for(unsigned status=0;status<8;status++){
   struct wr_iot_physical_stop_request request_out;
   unsigned long long serial=action==WR_STOP_ARM?0x200000003ULL:r.attempt;
   int valid=(action==WR_STOP_ARM&&status==WR_STOP_ARMED)||
    (action==WR_STOP_QUERY&&status>=WR_STOP_ARMED&&status<=WR_STOP_FAILED)||
    (action==WR_STOP_CANCEL&&status==WR_STOP_CANCELLED)||
    (action==WR_STOP_RELEASE&&status==WR_STOP_RELEASED);
   assert(wr_iot_physical_stop_response_encode(wire,64,&r,serial,status)==valid);
   if(!valid){for(unsigned i=0;i<64;i++)assert(!wire[i]);continue;}
   assert(wr_iot_physical_stop_response_decode(&out,wire,64,&r));
   assert(out.status==status&&out.identity.attempt==serial&&out.identity.action==action);
   assert(!wr_iot_physical_stop_request_decode(&request_out,wire,64));
   for(unsigned field=0;field<64;field++){
    int accepted;
    memcpy(bad,wire,64);bad[field]^=0x80;
    accepted=wr_iot_physical_stop_response_decode(&out,bad,64,&r);
    /* ARM assigns its new serial; exact subsequent QUERY must bind it. */
    if(action==WR_STOP_ARM&&field>=40&&field<48)continue;
    assert(!accepted&&!out.status&&!out.identity.attempt);
   }
   for(unsigned n=0;n<64;n++)assert(!wr_iot_physical_stop_response_decode(&out,wire,n,&r));
  }
 }
 r.action=WR_STOP_QUERY;r.attempt=7;
 assert(wr_iot_physical_stop_request_encode(wire,64,&r));
 assert(!wr_iot_physical_stop_response_decode(&out,wire,64,&r));
 assert(!wr_iot_physical_stop_response_encode(wire,64,&r,8,WR_STOP_COMPLETE));
 puts("PASS proposed typed stop response: exact echo/status/action, requests never decode as replies, stale field rejection, ARM serial assigned then bound by QUERY; no driver completion proof");
}
