#ifndef WR_IOT_PHYSICAL_REBIND_PROBE_H
#define WR_IOT_PHYSICAL_REBIND_PROBE_H
#include "radio-transition-api.h"
#include "physical-stop-origin.h"
#include "physical-rebind-probe-types.h"
/* Caller pins adapter/netdevices/PID and serializes begin/finish under transition
 * lock. Configuration readback runs unlocked under its own BcnRing protection.
 * Failed retirement retains active context; no caller may discard it. */

static inline int wr_iot_physical_rebind_request_equal(
 const struct wr_iot_physical_stop_request *a,const struct wr_iot_physical_stop_request *b)
{
 unsigned i;
 if(!wr_iot_physical_stop_request_valid(a)||!wr_iot_physical_stop_request_valid(b)||
    a->action!=b->action||a->attempt!=b->attempt||a->epoch!=b->epoch||
    a->generation!=b->generation||a->open_token!=b->open_token||a->closed_serial!=b->closed_serial)return 0;
 for(i=0;i<16;i++)if(a->nonce[i]!=b->nonce[i])return 0;
 return 1;
}
static inline int wr_iot_physical_rebind_probe_begin(
 struct wr_iot_physical_rebind_probe *p,
 const struct wr_iot_physical_stop_terminal *terminal,const struct pid *issuer,
 const struct wr_iot_physical_stop_request *request,
 const struct wr_iot_main_recovery_owner *owner,struct wr_iot_radio_transition *radio,
 struct wr_iot_interface_ref *slots,unsigned int count,
 const void *main_device,const void *iot_device,unsigned int vendor_count)
{
 struct wr_iot_interface_ref *main_record;
 if(!p||p->active||(p->spent&&wr_iot_physical_rebind_request_equal(&p->request,request))||
    !wr_iot_physical_stop_origin_pair(terminal,issuer,request,
    owner,radio,slots,count,main_device,iot_device,vendor_count))return 0;
 main_record=wr_iot_registry_find_owned(slots,count,main_device);
 if(!wr_iot_radio_begin(radio,radio->epoch,WR_RADIO_BSS_OBSERVE,&p->ticket))return 0;
 p->main_generation=main_record->generation;p->main_token=main_record->last_token;
 p->issuer=issuer;p->main_device=main_device;p->iot_device=iot_device;
 p->request=*request;p->accepted=0;p->spent=0;
 {unsigned i;for(i=0;i<16;i++)p->open_request_id[i]=0;}
 p->active=1;return 1;
}
static inline int wr_iot_physical_rebind_probe_finish(
 struct wr_iot_physical_rebind_probe *p,
 const struct wr_iot_physical_stop_terminal *terminal,const struct pid *issuer,
 const struct wr_iot_physical_stop_request *request,
 const struct wr_iot_main_recovery_owner *owner,struct wr_iot_radio_transition *radio,
 struct wr_iot_interface_ref *slots,unsigned int count,
 const void *main_device,const void *iot_device,unsigned int vendor_count,int observed)
{
 struct wr_iot_interface_ref *main_record;int accepted;unsigned i;
 if(!p||!p->active||!radio)return 0;
 accepted=observed==1&&radio->epoch==p->ticket.epoch&&issuer==p->issuer&&
  main_device==p->main_device&&iot_device==p->iot_device&&
  wr_iot_physical_stop_request_valid(request)&&request->action==p->request.action&&
  request->attempt==p->request.attempt&&request->epoch==p->request.epoch&&
  request->generation==p->request.generation&&request->open_token==p->request.open_token&&
  request->closed_serial==p->request.closed_serial;
 if(accepted)for(i=0;i<sizeof(request->nonce);i++)
  if(request->nonce[i]!=p->request.nonce[i]){accepted=0;break;}
 if(!wr_iot_radio_bss_observe_end(radio,&p->ticket))return 0;
 p->active=0;p->accepted=0;
 if(!accepted||!wr_iot_physical_stop_origin_pair(terminal,issuer,request,
    owner,radio,slots,count,main_device,iot_device,vendor_count))return 0;
 main_record=wr_iot_registry_find_owned(slots,count,main_device);
 p->accepted=main_record->generation==p->main_generation&&
  main_record->last_token==p->main_token;
 return p->accepted;
}
/* One-use host handoff claim, not OPEN/key/beacon acceptance. The final OPEN
 * binding must invoke this under the same transition lock as its own admission,
 * retain the claimed ID on uncertainty, and never restore accepted/spent bits. */
static inline int wr_iot_physical_rebind_claim(
 struct wr_iot_physical_rebind_probe *p,
 const struct wr_iot_physical_stop_terminal *terminal,const struct pid *issuer,
 const struct wr_iot_physical_stop_request *request,
 const struct wr_iot_main_recovery_owner *owner,struct wr_iot_radio_transition *radio,
 struct wr_iot_interface_ref *slots,unsigned int count,const void *main_device,
 const void *iot_device,unsigned int vendor_count,const unsigned char *open_id)
{
 unsigned i,nonzero=0;struct wr_iot_interface_ref *main_record;
 if(!p||p->active||p->accepted!=1||p->spent||!open_id||!radio||
    issuer!=p->issuer||main_device!=p->main_device||iot_device!=p->iot_device||
    !wr_iot_physical_rebind_request_equal(&p->request,request)||
    radio->epoch!=p->ticket.epoch||radio->serial!=p->ticket.serial||
    radio->retired_serial!=p->ticket.serial||
    !wr_iot_physical_stop_origin_pair(terminal,issuer,request,owner,radio,slots,
     count,main_device,iot_device,vendor_count))return 0;
 for(i=0;i<16;i++)nonzero|=open_id[i];
 if(!nonzero)return 0;
 main_record=wr_iot_registry_find_owned(slots,count,main_device);
 if(main_record->generation!=p->main_generation||main_record->last_token!=p->main_token)return 0;
 for(i=0;i<16;i++)p->open_request_id[i]=open_id[i];
 p->accepted=0;p->spent=1;return 1;
}
#endif
