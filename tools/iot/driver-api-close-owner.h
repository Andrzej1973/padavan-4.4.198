/* Isolated CLOSE ticket handoff. All calls hold adapter transition lock;
 * RTNL, task identity and netdev/adapter pins span the eventual executor.
 * No endpoint/ndo_stop binding or recovery release is implemented here. */
#ifndef WR_IOT_DRIVER_API_CLOSE_OWNER_H
#define WR_IOT_DRIVER_API_CLOSE_OWNER_H
#include "driver-api-close-admission.h"
struct wr_iot_driver_close_owner {
 struct wr_iot_radio_ticket ticket;
 const void *device,*task;
 const void *retirement_task;
 /* Mirrors the one prepare caller ref, not an additional task reference. */
 const void *retirement_handle;
 unsigned int retirement_started,retirement_canceling,retirement_entered;
 unsigned int retirement_module_transferred;
 int retirement_error;
 unsigned long generation,open_token;
 unsigned int active,consumed;
 unsigned int reference_completed,uncertain;
 unsigned int netdev_held,module_held,recovery_netdev_transferred;
 unsigned int recovery_join_pending,recovery_netdev_returned;
 unsigned int synchronous_put_pending,synchronous_netdev_returned;
};
/* Mutually exclusive origins of the extra API netdev reference return. */
static inline int wr_iot_driver_close_netdev_return_complete(
 const struct wr_iot_driver_close_owner *close)
{
 if(!close||close->netdev_held||close->recovery_join_pending||close->synchronous_put_pending)return 0;
 if(close->recovery_netdev_transferred)
  return close->recovery_netdev_returned&&!close->synchronous_netdev_returned;
 return !close->recovery_netdev_returned&&close->synchronous_netdev_returned&&
  close->reference_completed&&!close->uncertain;
}
/* Lifetime-only fence. Transfer marker is written only by designated thread
 * after locked readiness and a real same-origin dev_put receipt. Its local module
 * reference keeps text alive until core exit; it never accesses adapter again.
 * Active remains set to reject OPEN: this does not grant RF/isolation authority.
 * Inconsistent or partial transfer always retains adapter lifetime fence. */
static inline int wr_iot_driver_close_blocks_adapter_retirement(
 const struct wr_iot_driver_close_owner *close)
{
 if(!close||!close->active)return 0;
 return !close->retirement_module_transferred||!close->consumed||close->task||
  close->module_held||close->netdev_held||close->retirement_task||close->retirement_handle||
  close->retirement_started||close->retirement_entered||close->retirement_canceling||
  !wr_iot_driver_close_netdev_return_complete(close);
}
static inline int wr_iot_driver_close_reserve(
 struct wr_iot_driver_close_owner *close,const struct wr_iot_driver_owner *open,
 const unsigned char *nonce,struct wr_iot_radio_transition *radio,
 struct wr_iot_interface_ref *slots,unsigned int count,
 const void *main_dev,const void *iot_dev,const void *task,
 unsigned long epoch,unsigned long generation,unsigned long open_token,
 unsigned int vendor_count,unsigned int control_users,int control_blocked,int probe_active)
{
 struct wr_iot_radio_ticket ticket;struct wr_iot_interface_ref *record;
 if(!close||close->active||close->retirement_task||close->retirement_handle||!task||
    !wr_iot_driver_close_admissible(open,nonce,radio,slots,count,main_dev,iot_dev,
      epoch,generation,open_token,vendor_count,control_users,control_blocked,probe_active))return 0;
 record=wr_iot_registry_find_owned(slots,count,iot_dev);
 if(!wr_iot_radio_begin_stop(radio,vendor_count,&ticket))return 0;
 /* Admission excludes last-reference close; the existing executor consumes
  * the same recorded provenance, never another begin_close call. */
 record->close_epoch=ticket.epoch;record->close_vendor_count=vendor_count;
 record->close_prior_phase=(int)ticket.prior_phase;record->close_prior_ready=ticket.prior_ready;
 close->ticket=ticket;close->device=iot_dev;close->task=task;
 close->generation=generation;close->open_token=open_token;close->retirement_task=close->retirement_handle=0;
 close->retirement_started=close->retirement_canceling=close->retirement_entered=0;
 close->retirement_error=0;close->retirement_module_transferred=0;
 close->active=1;close->consumed=0;
 close->reference_completed=close->uncertain=0;
 close->netdev_held=close->module_held=close->recovery_netdev_transferred=0;
 close->recovery_join_pending=close->recovery_netdev_returned=0;
 close->synchronous_put_pending=close->synchronous_netdev_returned=0;return 1;
}
static inline int wr_iot_driver_close_take(
 struct wr_iot_driver_close_owner *close,const void *task,const void *dev,
 const struct wr_iot_radio_transition *radio,struct wr_iot_interface_ref *slots,
 unsigned int count,struct wr_iot_radio_ticket *ticket,unsigned long *generation)
{
 struct wr_iot_interface_ref *record;
 if(!close||!task||!dev||!radio||!ticket||!generation||!close->active||
    close->consumed||close->task!=task||close->device!=dev||
    close->ticket.operation!=WR_RADIO_BSS_CLOSE||close->ticket.reset_kind||
    radio->busy!=WR_RADIO_BSS_CLOSE||
    radio->epoch!=close->ticket.epoch||radio->serial!=close->ticket.serial)return 0;
 record=wr_iot_registry_find(slots,count,dev,close->generation);
 if(!record||!record->published||record->removing||record->removal_stage||record->family!=WR_REF_FAMILY_MBSS||
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
