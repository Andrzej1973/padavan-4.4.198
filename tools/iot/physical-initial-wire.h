/* Distinct Linux-only never-opened physical-stop transport. Not installed.
 * IDLE serial is an observation, never an OPEN token or CLOSE certificate. */
#ifndef WR_IOT_PHYSICAL_INITIAL_WIRE_H
#define WR_IOT_PHYSICAL_INITIAL_WIRE_H
#include "physical-stop-response.h"
struct wr_iot_physical_initial_request {
 unsigned action;
 unsigned long long epoch,generation,idle_serial,attempt;
 unsigned char nonce[16];
};
struct wr_iot_physical_initial_response {
 struct wr_iot_physical_initial_request identity;
 unsigned status;
};
static inline int wr_iot_physical_initial_valid(const struct wr_iot_physical_initial_request *r,int response)
{
 unsigned i,n=0;
 if(!r||r->action<WR_STOP_ARM||r->action>WR_STOP_RELEASE||!r->epoch||
    !r->generation||!r->idle_serial||
    ((response||r->action!=WR_STOP_ARM)?!r->attempt:r->attempt!=0))return 0;
 for(i=0;i<16;i++)n|=r->nonce[i];
 return n!=0;
}
static inline int wr_iot_physical_initial_encode(unsigned char *wire,unsigned length,
 const struct wr_iot_physical_initial_request *input,unsigned status)
{
 struct wr_iot_physical_initial_request r;unsigned i;
 if(!wire||length!=64)return 0;
 if(input)r=*input;
 for(i=0;i<length;i++)wire[i]=0;
 if(!input||!wr_iot_physical_initial_valid(&r,status!=0)||
    (status&&!wr_iot_physical_stop_status_valid(r.action,status)))return 0;
 wire[0]='W';wire[1]='P';wire[2]='I';wire[3]=status?'R':'Q';wire[4]=1;
 wire[5]=(unsigned char)r.action;wire[6]=(unsigned char)status;
 wr_iot_driver_put64(wire+8,r.epoch);wr_iot_driver_put64(wire+16,r.generation);
 wr_iot_driver_put64(wire+24,r.idle_serial);wr_iot_driver_put64(wire+32,r.attempt);
 for(i=0;i<16;i++)wire[40+i]=r.nonce[i];
 return 1;
}
static inline int wr_iot_physical_initial_decode(struct wr_iot_physical_initial_response *out,
 const unsigned char *wire,unsigned length,int response)
{
 struct wr_iot_physical_initial_response r={0};unsigned i;
 if(!out)return 0;
 if(wire&&length==64&&wire[0]=='W'&&wire[1]=='P'&&wire[2]=='I'&&
    wire[3]==(response?'R':'Q')&&wire[4]==1&&!wire[7]){
  for(i=56;i<64;i++)if(wire[i])goto fail;
  r.identity.action=wire[5];r.status=wire[6];
  r.identity.epoch=wr_iot_driver_get64(wire+8);
  r.identity.generation=wr_iot_driver_get64(wire+16);
  r.identity.idle_serial=wr_iot_driver_get64(wire+24);
  r.identity.attempt=wr_iot_driver_get64(wire+32);
  for(i=0;i<16;i++)r.identity.nonce[i]=wire[40+i];
  if(wr_iot_physical_initial_valid(&r.identity,response)&&
     (response?wr_iot_physical_stop_status_valid(r.identity.action,r.status):r.status==0)){
   *out=r;return 1;
  }
 }
 fail:r=(struct wr_iot_physical_initial_response){0};*out=r;return 0;
}
static inline int wr_iot_physical_initial_reply_matches(
 const struct wr_iot_physical_initial_response *r,
 const struct wr_iot_physical_initial_request *q)
{
 unsigned i;
 if(!r||!wr_iot_physical_initial_valid(q,0)||
    !wr_iot_physical_initial_valid(&r->identity,1)||
    !wr_iot_physical_stop_status_valid(q->action,r->status)||
    r->identity.action!=q->action||r->identity.epoch!=q->epoch||
    r->identity.generation!=q->generation||r->identity.idle_serial!=q->idle_serial||
    (q->action!=WR_STOP_ARM&&r->identity.attempt!=q->attempt))return 0;
 for(i=0;i<16;i++)if(r->identity.nonce[i]!=q->nonce[i])return 0;
 return 1;
}
#endif
