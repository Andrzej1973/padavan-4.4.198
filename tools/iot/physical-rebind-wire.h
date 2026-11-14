/* Linux-only envelope. No ioctl/firmware route installed by this codec.
 * Nonoverlapping buffers required. No native pointers or struct padding. */
#ifndef WR_IOT_PHYSICAL_REBIND_WIRE_H
#define WR_IOT_PHYSICAL_REBIND_WIRE_H
#include "physical-stop-wire.h"
#define WR_REBIND_OBSERVE 1U
#define WR_REBIND_OPEN 2U
#define WR_REBIND_OBSERVE_BYTES 72U
#define WR_REBIND_OPEN_BYTES 216U
struct wr_iot_physical_rebind_request {
 unsigned int operation;
 struct wr_iot_physical_stop_request physical;
 struct wr_iot_driver_open_request open;
};
static inline void wr_iot_physical_rebind_wipe(struct wr_iot_physical_rebind_request *r)
{
 volatile unsigned char *p=(volatile unsigned char *)r;unsigned i;
 if(r)for(i=0;i<sizeof(*r);i++)p[i]=0;
}
static inline int wr_iot_physical_rebind_decode(struct wr_iot_physical_rebind_request *out,
 const unsigned char *wire,unsigned length)
{
 struct wr_iot_physical_rebind_request r={0};int ok=0;
 if(!out)return 0;
 wr_iot_physical_rebind_wipe(out);
 if(!wire||(length!=72&&length!=216)||wire[0]!='W'||wire[1]!='R'||
    wire[2]!='R'||wire[3]!='B'||wire[4]!=1||wire[6]||wire[7])goto done;
 r.operation=wire[5];
 if((r.operation==WR_REBIND_OBSERVE&&length!=72)||
    (r.operation==WR_REBIND_OPEN&&length!=216)||
    (r.operation!=WR_REBIND_OBSERVE&&r.operation!=WR_REBIND_OPEN))goto done;
 if(!wr_iot_physical_stop_request_decode(&r.physical,wire+8,64)||
    r.physical.action!=WR_STOP_RELEASE)goto done;
 if(r.operation==WR_REBIND_OPEN){
  if(!wr_iot_driver_open_decode(&r.open,wire+72,144)||
     r.open.adapter_epoch<=r.physical.epoch||
     r.open.device_generation!=r.physical.generation)goto done;
 }
 *out=r;ok=1;
 done:wr_iot_physical_rebind_wipe(&r);return ok;
}
static inline int wr_iot_physical_rebind_encode(unsigned char *wire,unsigned length,
 const struct wr_iot_physical_rebind_request *r)
{
 struct wr_iot_physical_rebind_request checked={0};unsigned i;int ok=0;
 volatile unsigned char *wipe=wire;
 if(!wire||(length!=72&&length!=216))return 0;
 for(i=0;i<length;i++)wire[i]=0;
 if(!r||((r->operation!=WR_REBIND_OBSERVE||length!=72)&&
         (r->operation!=WR_REBIND_OPEN||length!=216)))goto done;
 wire[0]='W';wire[1]='R';wire[2]='R';wire[3]='B';wire[4]=1;wire[5]=r->operation;
 if(!wr_iot_physical_stop_request_encode(wire+8,64,&r->physical))goto done;
 if(r->operation==WR_REBIND_OPEN&&!wr_iot_driver_open_encode(wire+72,144,&r->open))goto done;
 ok=wr_iot_physical_rebind_decode(&checked,wire,length);
 done:wr_iot_physical_rebind_wipe(&checked);
 if(!ok)for(i=0;i<length;i++)wipe[i]=0;
 return ok;
}
#endif
