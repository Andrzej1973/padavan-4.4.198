/* All functions require the existing adapter transition lock. Caller pins
 * adapter/netdev lifetime under RTNL. The stored task pointer is borrowed only
 * for this synchronous ioctl; leave always clears it and credential bytes.
 * No mutation or permission is granted by this uninstalled header alone. */
#ifndef WR_IOT_DRIVER_API_OWNER_H
#define WR_IOT_DRIVER_API_OWNER_H
#include "driver-api-wire.h"
#include "radio-transition-api.h"
#include "virtual-open-claim.h"
/* Nonsecret identity only; device pointer is compared, never dereferenced and
 * never substitutes for a netdev/lifetime pin or current registry check. */
struct wr_iot_driver_open_receipt {
 const void *device;
 unsigned long epoch,generation,open_token;
 unsigned char request_id[16];
 unsigned int valid;
};
struct wr_iot_driver_owner {
 struct wr_iot_driver_open_request request;
 struct wr_iot_virtual_open_claim claim;
 struct wr_iot_radio_ticket ticket;
 const void *task;
 unsigned int active,consumed,poisoned,query_valid;
 unsigned char query_id[16];
 unsigned long long query_epoch,query_generation;
 struct wr_iot_driver_open_receipt receipt;
};
/* Called under transition lock after current adapter identity observation.
 * Challenge metadata is not a task/netdev pin and grants no radio permission. */
static inline int wr_iot_driver_owner_query(struct wr_iot_driver_owner *o,
 const unsigned char *id,unsigned long long epoch,unsigned long long generation){
 unsigned int i,nonzero=0;
 if(!o||!id||o->active||o->poisoned||!epoch||!generation)return 0;
 for(i=0;i<16;i++)nonzero|=id[i];
 if(!nonzero)return 0;
 for(i=0;i<16;i++)o->query_id[i]=id[i];
 o->query_epoch=epoch;o->query_generation=generation;o->query_valid=1;return 1;
}
static inline void wr_iot_driver_owner_query_drop(struct wr_iot_driver_owner *o,
 const unsigned char *id,unsigned long long epoch,unsigned long long generation){
 unsigned int i,difference=0;
 if(!o||!id||o->query_epoch!=epoch||o->query_generation!=generation)return;
 for(i=0;i<16;i++)difference|=o->query_id[i]^id[i];
 if(difference)return;
 o->query_valid=0;
 for(i=0;i<16;i++)o->query_id[i]=0;
}
static inline int wr_iot_driver_owner_reserve(struct wr_iot_driver_owner *o,
 struct wr_iot_radio_transition *radio,struct wr_iot_interface_ref *slots,
 unsigned int count,const void *main_dev,const void *iot_dev,
 unsigned int vendor_count,const void *task,
 const struct wr_iot_driver_open_request *request,unsigned int control_users,
 int control_blocked)
{
 struct wr_iot_interface_ref *main_ref,*record;unsigned int i,difference=0;
 if(!o||!radio||!request||!task||!iot_dev||iot_dev==main_dev||o->active||
    o->poisoned||control_users||control_blocked)return 0;
 if(!o->query_valid||request->adapter_epoch!=o->query_epoch||
    request->device_generation!=o->query_generation)return 0;
 for(i=0;i<16;i++)difference|=request->request_id[i]^o->query_id[i];
 if(difference)return 0;
 main_ref=wr_iot_registry_find_owned(slots,count,main_dev);
 record=wr_iot_registry_find_openable(slots,count,iot_dev);
 if(!main_ref||main_ref->family!=WR_REF_FAMILY_MAIN||main_ref->removing||
    !record||record->family!=WR_REF_FAMILY_MBSS||!vendor_count||
    !wr_iot_registry_count_matches(slots,count,vendor_count)||
    request->adapter_epoch!=radio->epoch||
    request->device_generation!=record->generation)return 0;
 if(!wr_iot_radio_begin(radio,radio->epoch,WR_RADIO_BSS_OPEN,&o->ticket))return 0;
 if(!wr_iot_ref_reserve(record,iot_dev,record->generation,o->ticket.serial)){
  wr_iot_radio_abort_bss_open_unmutated(radio,&o->ticket);return 0;
 }
 o->query_valid=0;
 o->request=*request;o->task=task;o->active=1;o->consumed=0;
 o->claim.device=iot_dev;o->claim.generation=record->generation;
 o->claim.serial=o->ticket.serial;o->claim.epoch=o->ticket.epoch;
 o->claim.operation=WR_RADIO_BSS_OPEN;return 1;
}
/* Borrowed read-only request remains valid until synchronous owner leave.
 * Caller must compare credentials outside the spinlock, then revalidate the
 * same claim before mutation. This function does not perform that comparison. */
static inline const struct wr_iot_driver_open_request *wr_iot_driver_owner_take(
 struct wr_iot_driver_owner *o,const void *task,const void *dev,
 const struct wr_iot_radio_transition *radio,
 struct wr_iot_interface_ref *slots,unsigned int count)
{
 if(!o||!o->active||o->poisoned||o->consumed||o->task!=task||
    o->claim.device!=dev||!wr_iot_virtual_open_claim_matches(&o->claim,radio,slots,count))return 0;
 o->consumed=1;return &o->request;
}
static inline int wr_iot_driver_owner_leave(struct wr_iot_driver_owner *o,
 const void *task,const void *dev,struct wr_iot_radio_transition *radio,
 struct wr_iot_interface_ref *slots,unsigned int count)
{
 struct wr_iot_interface_ref *record;unsigned int i;int clean;
 struct wr_iot_radio_ticket retained_ticket;
 struct wr_iot_virtual_open_claim retained_claim;
 struct wr_iot_driver_open_receipt retained_receipt;
 volatile unsigned char *wipe;
 if(!o||!radio||!o->active||o->task!=task||o->claim.device!=dev)return 0;
 /* dev_open can fail before ndo_open. Cancel only a still-current unconsumed
  * reservation, never an attempted vendor mutation or a changed generation. */
 if(!o->consumed&&wr_iot_virtual_open_claim_matches(&o->claim,radio,slots,count)){
  record=wr_iot_registry_find(slots,count,dev,o->claim.generation);
  if(wr_iot_ref_open_finish(record,dev,o->claim.generation,o->claim.serial,0))
   wr_iot_radio_abort_bss_open_unmutated(radio,&o->ticket);
 }
 record=wr_iot_registry_find(slots,count,dev,o->claim.generation);
 clean=!o->poisoned&&!radio->busy&&radio->retired_serial==o->ticket.serial&&
  radio->phase==WR_RADIO_READY&&radio->main_ready&&!radio->main_inhibited&&
  radio->epoch==o->claim.epoch&&!radio->reset_pending&&!radio->retiring&&
  !radio->pm_suspending&&!radio->pm_suspended&&record&&!record->removing;
 retained_ticket=o->ticket;retained_claim=o->claim;
 retained_receipt=o->receipt;
 if(clean&&o->consumed&&record->phase==WR_REF_OWNED&&record->published&&
    record->family==WR_REF_FAMILY_MBSS&&record->last_token==o->claim.serial){
  retained_receipt.device=dev;retained_receipt.epoch=o->claim.epoch;
  retained_receipt.generation=o->claim.generation;retained_receipt.open_token=o->claim.serial;
  for(i=0;i<16;i++)retained_receipt.request_id[i]=o->request.request_id[i];
  retained_receipt.valid=1;
 }else if(!clean)retained_receipt.valid=0;
 wipe=(volatile unsigned char *)o;
 for(i=0;i<sizeof(*o);i++)wipe[i]=0;
 o->poisoned=!clean;
 o->receipt=retained_receipt;
 /* Keep nonsecret recovery identity on uncertainty, never a borrowed task
  * pointer or credentials. This metadata does not pin the netdev lifetime. */
 if(!clean){o->ticket=retained_ticket;o->claim=retained_claim;}
 return clean;
}
/* Caller additionally verifies exact current registry/close receipt under the
 * same transition lock. This helper alone grants no current-state permission. */
static inline int wr_iot_driver_open_receipt_matches(const struct wr_iot_driver_owner *o,
 const unsigned char *id,const void *dev,unsigned long epoch,
 unsigned long generation,unsigned long open_token){
 unsigned int i,difference=0;
 if(!o||!id||o->active||o->poisoned||!o->receipt.valid||!dev||
    o->receipt.device!=dev||o->receipt.epoch!=epoch||
    o->receipt.generation!=generation||o->receipt.open_token!=open_token)return 0;
 for(i=0;i<16;i++)difference|=id[i]^o->receipt.request_id[i];
 return difference==0;
}
#endif
