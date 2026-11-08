/* All functions require the existing adapter transition lock. Caller pins
 * adapter/netdev lifetime under RTNL. The stored task pointer is borrowed only
 * for this synchronous ioctl; leave always clears it and credential bytes.
 * No mutation or permission is granted by this uninstalled header alone. */
#ifndef WR_IOT_DRIVER_API_OWNER_H
#define WR_IOT_DRIVER_API_OWNER_H
#include "driver-api-wire.h"
#include "virtual-open-claim.h"
struct wr_iot_driver_owner {
 struct wr_iot_driver_open_request request;
 struct wr_iot_virtual_open_claim claim;
 struct wr_iot_radio_ticket ticket;
 const void *task;
 unsigned int active,consumed,poisoned;
};
static inline int wr_iot_driver_owner_reserve(struct wr_iot_driver_owner *o,
 struct wr_iot_radio_transition *radio,struct wr_iot_interface_ref *slots,
 unsigned int count,const void *main_dev,const void *iot_dev,
 unsigned int vendor_count,const void *task,
 const struct wr_iot_driver_open_request *request,unsigned int control_users,
 int control_blocked)
{
 struct wr_iot_interface_ref *main_ref,*record;
 if(!o||!radio||!request||!task||!iot_dev||iot_dev==main_dev||o->active||
    o->poisoned||control_users||control_blocked)return 0;
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
 wipe=(volatile unsigned char *)o;
 for(i=0;i<sizeof(*o);i++)wipe[i]=0;
 o->poisoned=!clean;
 /* Keep nonsecret recovery identity on uncertainty, never a borrowed task
  * pointer or credentials. This metadata does not pin the netdev lifetime. */
 if(!clean){o->ticket=retained_ticket;o->claim=retained_claim;}
 return clean;
}
#endif
