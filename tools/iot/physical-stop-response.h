/* Proposed Linux-only response. Binding must derive state from actual owned
 * record; wire syntax itself cannot certify driver/RF/DMA completion. */
#ifndef WR_IOT_PHYSICAL_STOP_RESPONSE_H
#define WR_IOT_PHYSICAL_STOP_RESPONSE_H
#include "physical-stop-wire.h"
enum wr_iot_physical_stop_status {WR_STOP_ARMED=1,WR_STOP_RUNNING,
 WR_STOP_COMPLETE,WR_STOP_FAILED,WR_STOP_CANCELLED,WR_STOP_RELEASED};
struct wr_iot_physical_stop_response {
 struct wr_iot_physical_stop_request identity;
 unsigned int status;
};
static inline int wr_iot_physical_stop_status_valid(unsigned int action,unsigned int status)
{
 if(action==WR_STOP_ARM)return status==WR_STOP_ARMED;
 if(action==WR_STOP_QUERY)return status>=WR_STOP_ARMED&&status<=WR_STOP_FAILED;
 if(action==WR_STOP_CANCEL)return status==WR_STOP_CANCELLED;
 if(action==WR_STOP_RELEASE)return status==WR_STOP_RELEASED;
 return 0;
}
static inline int wr_iot_physical_stop_response_encode(unsigned char *wire,unsigned int length,
 const struct wr_iot_physical_stop_request *request,unsigned long long attempt,unsigned int status)
{
 struct wr_iot_physical_stop_request encoded;unsigned i,action;
 if(!wire||length!=64)return 0;
 if(request)encoded=*request;
 for(i=0;i<length;i++)wire[i]=0;
 if(!request||!wr_iot_physical_stop_request_valid(&encoded)||!attempt||
    (encoded.action!=WR_STOP_ARM&&encoded.attempt!=attempt)||
    !wr_iot_physical_stop_status_valid(encoded.action,status))return 0;
 /* Reuse payload serialization as QUERY, then set distinct response type. */
 action=encoded.action;encoded.action=WR_STOP_QUERY;encoded.attempt=attempt;
 if(!wr_iot_physical_stop_request_encode(wire,length,&encoded))return 0;
 wire[3]='R';wire[5]=(unsigned char)action;wire[6]=(unsigned char)status;return 1;
}
static inline int wr_iot_physical_stop_response_decode(struct wr_iot_physical_stop_response *out,
 const unsigned char *wire,unsigned int length,const struct wr_iot_physical_stop_request *expected)
{
 struct wr_iot_physical_stop_response candidate={0};unsigned char copy[64];unsigned i,action;
 if(!out)return 0;
 if(wire&&length==64&&expected&&wr_iot_physical_stop_request_valid(expected)&&
    wire[3]=='R'&&wire[5]==expected->action&&
    wr_iot_physical_stop_status_valid(wire[5],wire[6])){
  for(i=0;i<64;i++)copy[i]=wire[i];
  action=wire[5];candidate.status=wire[6];
  copy[3]='Q';copy[5]=WR_STOP_QUERY;copy[6]=0;
  if(wr_iot_physical_stop_request_decode(&candidate.identity,copy,64)&&
     candidate.identity.epoch==expected->epoch&&candidate.identity.generation==expected->generation&&
     candidate.identity.open_token==expected->open_token&&candidate.identity.closed_serial==expected->closed_serial&&
     (action==WR_STOP_ARM||candidate.identity.attempt==expected->attempt)){
   for(i=0;i<16;i++)if(candidate.identity.nonce[i]!=expected->nonce[i])break;
   if(i==16){candidate.identity.action=action;*out=candidate;return 1;}
  }
 }
 {struct wr_iot_physical_stop_response empty={0};*out=empty;}return 0;
}
#endif
