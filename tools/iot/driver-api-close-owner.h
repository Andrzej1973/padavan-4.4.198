/* Isolated CLOSE ticket handoff. All calls hold adapter transition lock;
 * RTNL, task identity and netdev/adapter pins span the eventual executor.
 * No endpoint/ndo_stop binding or recovery release is implemented here. */
#ifndef WR_IOT_DRIVER_API_CLOSE_OWNER_H
#define WR_IOT_DRIVER_API_CLOSE_OWNER_H
#include "driver-api-close-admission.h"
struct wr_iot_driver_close_owner {
 struct wr_iot_radio_ticket ticket;
 const void *device,*task;
 unsigned long generation,open_token;
 unsigned int active,consumed;
};
static inline int wr_iot_driver_close_reserve(
 struct wr_iot_driver_close_owner *close,const struct wr_iot_driver_owner *open,
 const unsigned char *nonce,struct wr_iot_radio_transition *radio,
 struct wr_iot_interface_ref *slots,unsigned int count,
 const void *main_dev,const void *iot_dev,const void *task,
 unsigned long epoch,unsigned long generation,unsigned long open_token,
 unsigned int vendor_count,unsigned int control_users,int control_blocked,int probe_active)
{
 struct wr_iot_radio_ticket ticket;struct wr_iot_interface_ref *record;
 if(!close||close->active||!task||
    !wr_iot_driver_close_admissible(open,nonce,radio,slots,count,main_dev,iot_dev,
      epoch,generation,open_token,vendor_count,control_users,control_blocked,probe_active))return 0;
 record=wr_iot_registry_find_owned(slots,count,iot_dev);
 if(!wr_iot_radio_begin_stop(radio,vendor_count,&ticket))return 0;
 /* Admission excludes last-reference close; the existing executor consumes
  * the same recorded provenance, never another begin_close call. */
 record->close_epoch=ticket.epoch;record->close_vendor_count=vendor_count;
 record->close_prior_phase=(int)ticket.prior_phase;record->close_prior_ready=ticket.prior_ready;
 close->ticket=ticket;close->device=iot_dev;close->task=task;
 close->generation=generation;close->open_token=open_token;
 close->active=1;close->consumed=0;return 1;
}
static inline int wr_iot_driver_close_take(
 struct wr_iot_driver_close_owner *close,const void *task,const void *dev,
 const struct wr_iot_radio_transition *radio,struct wr_iot_interface_ref *slots,
 unsigned int count,struct wr_iot_radio_ticket *ticket,unsigned long *generation)
{
 struct wr_iot_interface_ref *record;
 if(!close||!task||!dev||!radio||!ticket||!generation||!close->active||
    close->consumed||close->task!=task||close->device!=dev||
    close->ticket.operation!=WR_RADIO_BSS_CLOSE||radio->busy!=WR_RADIO_BSS_CLOSE||
    radio->epoch!=close->ticket.epoch||radio->serial!=close->ticket.serial)return 0;
 record=wr_iot_registry_find(slots,count,dev,close->generation);
 if(!record||!record->published||record->removing||record->family!=WR_REF_FAMILY_MBSS||
    record->phase!=WR_REF_OWNED||record->last_token!=close->open_token||
    record->close_epoch!=close->ticket.epoch||record->close_vendor_count<=1||
    record->close_prior_phase!=(int)close->ticket.prior_phase||
    record->close_prior_ready!=close->ticket.prior_ready||record->close_running||
    record->close_uncertain_reason)return 0;
 *ticket=close->ticket;*generation=close->generation;close->consumed=1;return 1;
}
/* No release helper: a missing callback, failed take or executor failure keeps
 * this exact ticket/provenance. Recovery must prove completion before release.
 * Administrative DOWN or dev_close's return is never that proof. */
#endif
