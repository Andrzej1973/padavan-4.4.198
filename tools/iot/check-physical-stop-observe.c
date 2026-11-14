#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "physical-stop-observe.h"
int main(void){
 int task,foreign;unsigned char wire[64];
 struct wr_iot_physical_stop_record record={0};
 struct wr_iot_peer_close_executor executor={0};
 struct wr_iot_peer_table_owner table;
 wr_iot_peer_table_owner_init(&table);
 unsigned long s=wr_iot_peer_table_begin(&table);assert(s&&wr_iot_peer_table_close_seal(&table,s));
 struct wr_iot_physical_stop_request request={.action=WR_STOP_ARM,.epoch=1,.generation=2,.open_token=3,.closed_serial=0x100000004ULL,.nonce={1}};
 assert(!wr_iot_physical_stop_record_reply(wire,64,&record,&request,&task,1,2));
 assert(wr_iot_physical_stop_arm(&record,1,2,3,request.closed_serial,request.nonce,&task,&executor));
 assert(wr_iot_physical_stop_record_reply(wire,64,&record,&request,&task,1,2));
 struct wr_iot_physical_stop_response reply;
 assert(wr_iot_physical_stop_response_decode(&reply,wire,64,&request)&&reply.status==WR_STOP_ARMED);
 request.action=WR_STOP_QUERY;request.attempt=reply.identity.attempt;
 for(unsigned phase=0;phase<4;phase++){
  struct wr_iot_physical_stop_record observed=record;
  if(phase){assert(wr_iot_physical_stop_begin(&observed,1,1,2,request.nonce,&task));}
  if(phase>=2)assert(wr_iot_physical_stop_finish(&observed,1,1,2,request.nonce,&task,phase==2,&executor,&table,2)==(phase==2));
  struct wr_iot_physical_stop_record before=observed;
  assert(wr_iot_physical_stop_record_reply(wire,64,&observed,&request,&task,1,2));
  assert(wr_iot_physical_stop_response_decode(&reply,wire,64,&request));
  assert(reply.status==phase+1);
  assert(!wr_iot_physical_stop_record_reply(wire,64,&observed,&request,&foreign,1,2));
  assert(!wr_iot_physical_stop_record_reply(wire,64,&observed,&request,&task,9,2));
  assert(!wr_iot_physical_stop_record_reply(wire,64,&observed,&request,&task,1,9));
  request.open_token++;assert(!wr_iot_physical_stop_record_reply(wire,64,&observed,&request,&task,1,2));request.open_token--;
  request.closed_serial++;assert(!wr_iot_physical_stop_record_reply(wire,64,&observed,&request,&task,1,2));request.closed_serial--;
  request.attempt++;assert(!wr_iot_physical_stop_record_reply(wire,64,&observed,&request,&task,1,2));request.attempt--;
  request.nonce[0]++;assert(!wr_iot_physical_stop_record_reply(wire,64,&observed,&request,&task,1,2));request.nonce[0]--;
  for(unsigned i=0;i<64;i++)assert(!wire[i]);
  assert(!memcmp(&before,&observed,sizeof(before)));
  if(phase==2){
   assert(wr_iot_physical_stop_release(&observed,request.attempt,1,2,request.nonce,&task));
   assert(!wr_iot_physical_stop_record_reply(wire,64,&observed,&request,&task,1,2));
   struct wr_iot_physical_stop_request next=request;next.action=WR_STOP_ARM;next.attempt=0;next.nonce[0]=2;
   assert(wr_iot_physical_stop_arm(&observed,1,2,3,next.closed_serial,next.nonce,&task,&executor));
   assert(!wr_iot_physical_stop_record_reply(wire,64,&observed,&request,&task,1,2));
   assert(wr_iot_physical_stop_record_reply(wire,64,&observed,&next,&task,1,2));
   assert(wr_iot_physical_stop_response_decode(&reply,wire,64,&next)&&reply.status==WR_STOP_ARMED&&reply.identity.attempt==2);
   next.action=WR_STOP_RELEASE;next.attempt=2;
   assert(!wr_iot_physical_stop_record_reply(wire,64,&observed,&next,&task,1,2));
   next.action=WR_STOP_CANCEL;
   assert(!wr_iot_physical_stop_record_reply(wire,64,&observed,&next,&task,1,2));
  }

 }
 struct wr_iot_physical_stop_record transitioned={0};
 request.action=WR_STOP_ARM;request.attempt=0;
 assert(wr_iot_physical_stop_arm(&transitioned,1,2,3,request.closed_serial,request.nonce,&task,&executor));
 assert(wr_iot_physical_stop_begin(&transitioned,1,1,2,request.nonce,&task));
 assert(wr_iot_physical_stop_finish_at_epoch(&transitioned,1,1,2,request.nonce,&task,1,&executor,&table,2,2));
 request.action=WR_STOP_QUERY;request.attempt=1;
 assert(!wr_iot_physical_stop_record_reply(wire,64,&transitioned,&request,&task,1,2));
 assert(wr_iot_physical_stop_record_reply(wire,64,&transitioned,&request,&task,2,2));
 assert(wr_iot_physical_stop_response_decode(&reply,wire,64,&request)&&reply.status==WR_STOP_COMPLETE);
 assert(!wr_iot_physical_stop_record_reply(wire,64,&transitioned,&request,&task,3,2));
 puts("PASS actual record-to-reply: ARM plus4 QUERY phases, completion from actual record lifecycle, stale live identity/task/token/serial/nonce refuse with cleared output, bytewise read-only; endpoint/locking unbound");
}
