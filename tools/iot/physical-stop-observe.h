/* Locked kernel-side record-to-wire observation; not an installed endpoint.
 * Caller supplies fresh epoch/generation under their actual owner lock and
 * serializes the record for the whole observation. Never pass cached identity
 * as live identity. No waits, user copy, resource release or state mutation. */
#ifndef WR_IOT_PHYSICAL_STOP_OBSERVE_H
#define WR_IOT_PHYSICAL_STOP_OBSERVE_H
#include "physical-stop-record.h"
#include "physical-stop-response.h"
static inline int wr_iot_physical_stop_record_reply(unsigned char *wire,unsigned int length,
 const struct wr_iot_physical_stop_record *record,
 const struct wr_iot_physical_stop_request *request,const void *task,
 unsigned long long live_epoch,unsigned long long live_generation)
{
 unsigned int i,status=0;
 if(!wire||length!=64)return 0;
 for(i=0;i<length;i++)wire[i]=0;
 if(!record||!wr_iot_physical_stop_request_valid(request)||!task||
    request->epoch!=record->epoch||request->generation!=live_generation||
    record->generation!=live_generation||
    live_epoch!=(record->phase==WR_PHYS_STOP_COMPLETE?record->completion_epoch:record->epoch)||
    record->open_token!=request->open_token||record->closed_serial!=request->closed_serial||
    !wr_iot_physical_stop_matches(record,record->serial,record->epoch,live_generation,request->nonce,task))return 0;
 if(request->action==WR_STOP_ARM){
  if(record->phase!=WR_PHYS_STOP_ARMED)return 0;
  status=WR_STOP_ARMED;
 }else if(request->action==WR_STOP_QUERY){
  if(request->attempt!=record->serial)return 0;
  switch(record->phase){
  case WR_PHYS_STOP_ARMED:status=WR_STOP_ARMED;break;
  case WR_PHYS_STOP_RUNNING:status=WR_STOP_RUNNING;break;
  case WR_PHYS_STOP_COMPLETE:
   if(!wr_iot_physical_stop_observe(record,request->attempt,record->epoch,live_generation,
                                    request->open_token,request->closed_serial,request->nonce,task))return 0;
   status=WR_STOP_COMPLETE;break;
  case WR_PHYS_STOP_FAILED:status=WR_STOP_FAILED;break;
  default:return 0;
  }
 }else return 0; /* Cancel/release require their own retained result publication. */
 return wr_iot_physical_stop_response_encode(wire,length,request,record->serial,status);
}
#endif
